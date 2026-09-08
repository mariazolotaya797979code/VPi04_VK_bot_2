from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.exceptions import ApiError
from vk_api.utils import get_random_id

import config
from catalog import (
    SERVICES_BY_KEY,
    find_service,
    format_price_list,
    format_service,
    format_services,
)
from http_setup import no_proxy_session
from keyboards import (
    BTN_BACK,
    BTN_BACK_SERVICES,
    BTN_MANAGER,
    BTN_MENU,
    BTN_PRICES,
    BTN_SERVICES,
    main_keyboard,
    manager_keyboard,
    prices_keyboard,
    service_keyboard,
    services_keyboard,
)

logger = logging.getLogger(__name__)

VK_TEXT_LIMIT = 4096
CHAT_PEER_OFFSET = 2_000_000_000

START_ALIASES = {
    "start",
    "/start",
    "начать",
    "привет",
    "здравствуйте",
    "здравствуй",
    "добрый день",
    "добрый вечер",
    "доброе утро",
    "меню",
    "главное меню",
    "назад",
}

GREETING = (
    f"Здравствуйте! Это {config.STUDIO_NAME} — студия детейлинга автомобилей.\n\n"
    "Помогаем с химчисткой салона, полировкой кузова и керамическим покрытием.\n\n"
    "Выберите раздел на клавиатуре ниже."
)

UNKNOWN_TEXT = (
    "Не совсем понял запрос. Откройте «Услуги», «Прайс-лист» "
    "или «Связаться с менеджером» — кнопки под полем ввода."
)

AS_COMMUNITY_HINT = (
    "Сейчас сообщение пришло от имени сообщества, а не от пользователя. "
    "Переключитесь на «писать как пользователь» и снова отправьте «начать»."
)

REQUEST_THANKS = (
    "Спасибо! Запрос передан. Менеджер ответит в этом чате в ближайшее время."
)


def mention_re() -> re.Pattern[str]:
    return re.compile(rf"\[club{config.VK_GROUP_ID}\|.*?\]", re.IGNORECASE)


def _field(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_message(event: Any) -> dict[str, Any]:
    raw = event.object
    message = _field(raw, "message", raw)
    payload = _field(message, "payload")
    if isinstance(payload, str) and payload:
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {"raw": payload}
    return {
        "text": (_field(message, "text") or "").strip(),
        "peer_id": _field(message, "peer_id"),
        "from_id": _field(message, "from_id"),
        "out": int(_field(message, "out", 0) or 0),
        "payload": payload if isinstance(payload, dict) else {},
        "reply_message": _field(message, "reply_message"),
        "action": _field(message, "action"),
    }


def is_chat(peer_id: int) -> bool:
    return peer_id >= CHAT_PEER_OFFSET


def strip_mention(text: str) -> str:
    return mention_re().sub("", text).strip()


def split_text(text: str) -> list[str]:
    if len(text) <= VK_TEXT_LIMIT:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        chunks.append(rest[:VK_TEXT_LIMIT])
        rest = rest[VK_TEXT_LIMIT:]
    return chunks


def manager_contact_text() -> str:
    parts = [
        "Связаться с менеджером:",
        "",
    ]
    if config.MANAGER_ID.isdigit():
        parts.append(f"Напишите: [id{config.MANAGER_ID}|менеджеру студии]")
    if config.MANAGER_URL:
        parts.append(f"Или перейдите по ссылке: {config.MANAGER_URL}")
    if not config.MANAGER_ID.isdigit() and not config.MANAGER_URL:
        parts.append(
            "Опишите запрос прямо в этом чате — марка/модель авто и нужная услуга. "
            "Менеджер ответит вам здесь."
        )
    else:
        parts.append(
            "Можно также написать запрос сюда: марка автомобиля и какая услуга нужна."
        )
    return "\n".join(parts)


class DetailingBot:
    def __init__(self) -> None:
        if not config.VK_GROUP_ID:
            raise SystemExit("Не задан VK_GROUP_ID в .env")
        self.session = vk_api.VkApi(
            token=config.VK_TOKEN,
            api_version=config.VK_API_VERSION,
        )
        no_proxy_session(self.session.http)
        self.vk = self.session.get_api()
        self.enable_longpoll_events()
        self.enable_bot_features()
        self.longpoll = self._make_longpoll()
        self.keyboard = main_keyboard()
        self.awaiting_request: set[int] = set()
        self.seen_peers: set[int] = set()

    def _make_longpoll(self) -> VkBotLongPoll:
        longpoll = VkBotLongPoll(self.session, config.VK_GROUP_ID)
        no_proxy_session(longpoll.session)
        return longpoll

    def enable_longpoll_events(self) -> None:
        try:
            self.vk.groups.setLongPollSettings(
                group_id=config.VK_GROUP_ID,
                enabled=1,
                api_version=config.VK_API_VERSION,
                message_new=1,
            )
            logger.info("Bots Long Poll API включён, событие message_new активно")
        except ApiError as exc:
            logger.warning(
                "Не удалось автоматически включить Long Poll (%s). "
                "Включите вручную: Управление → Работа с API → Long Poll API",
                exc,
            )

    def enable_bot_features(self) -> None:
        try:
            self.vk.groups.setSettings(
                group_id=config.VK_GROUP_ID,
                messages=1,
                bots_capabilities=1,
                bots_start_button=1,
            )
            logger.info("Сообщения и возможности ботов включены (groups.setSettings)")
        except ApiError as exc:
            logger.warning(
                "Не удалось включить «Возможности ботов» через API (%s). "
                "Включите вручную: Управление → Сообщения → Настройки для бота. "
                "Иначе VK отклонит клавиатуру с ошибкой 912.",
                exc,
            )

    def send(self, peer_id: int, text: str, keyboard: str | None = None) -> None:
        kb = self.keyboard if keyboard is None else keyboard
        for chunk in split_text(text):
            self._send_chunk(peer_id, chunk, kb)

    def _send_chunk(self, peer_id: int, text: str, keyboard: str | None) -> None:
        params: dict[str, Any] = {
            "peer_id": peer_id,
            "message": text,
            "random_id": get_random_id(),
        }
        use_kb = bool(keyboard) and not is_chat(peer_id)
        if use_kb:
            params["keyboard"] = keyboard
        try:
            self.vk.messages.send(**params)
        except ApiError as exc:
            if use_kb and (exc.code == 912 or "chat bot" in str(exc).lower()):
                logger.warning(
                    "Клавиатура отклонена VK (%s). Отправляю текст без кнопок.",
                    exc,
                )
                params.pop("keyboard", None)
                params["random_id"] = get_random_id()
                self.vk.messages.send(**params)
                return
            logger.exception("Не удалось отправить сообщение peer_id=%s", peer_id)
            raise

    def show_menu(self, peer_id: int) -> None:
        self.awaiting_request.discard(peer_id)
        self.send(peer_id, GREETING, main_keyboard())

    def show_services(self, peer_id: int) -> None:
        self.awaiting_request.discard(peer_id)
        self.send(peer_id, format_services(), services_keyboard())

    def show_prices(self, peer_id: int) -> None:
        self.awaiting_request.discard(peer_id)
        self.send(peer_id, format_price_list(), prices_keyboard())

    def show_service(self, peer_id: int, key: str) -> bool:
        item = SERVICES_BY_KEY.get(key)
        if item is None:
            return False
        self.awaiting_request.discard(peer_id)
        self.send(peer_id, format_service(item), service_keyboard())
        return True

    def show_manager(self, peer_id: int) -> None:
        self.awaiting_request.add(peer_id)
        self.send(peer_id, manager_contact_text(), manager_keyboard())

    def handle_menu(self, peer_id: int, text: str, payload: dict[str, Any]) -> bool:
        cmd = str(payload.get("cmd", "")).lower()
        key = str(payload.get("key", "")).strip()
        lowered = text.lower().lstrip("/")
        normalized = " ".join(lowered.split())

        if cmd == "menu" or normalized in START_ALIASES:
            self.show_menu(peer_id)
            return True

        if cmd == "services" or text == BTN_SERVICES or normalized in {"услуги", "каталог"}:
            self.show_services(peer_id)
            return True

        if cmd == "prices" or text == BTN_PRICES or normalized in {
            "прайс-лист",
            "прайс",
            "цены",
            "price",
        }:
            self.show_prices(peer_id)
            return True

        if cmd == "manager" or text == BTN_MANAGER or normalized in {
            "связаться с менеджером",
            "менеджер",
            "контакт",
            "контакты",
        }:
            self.show_manager(peer_id)
            return True

        if cmd == "service" and key:
            return self.show_service(peer_id, key)

        if text in {BTN_BACK, BTN_BACK_SERVICES, BTN_MENU}:
            if text == BTN_BACK_SERVICES:
                self.show_services(peer_id)
            else:
                self.show_menu(peer_id)
            return True

        matched = find_service(text)
        if matched is not None:
            return self.show_service(peer_id, matched.key)

        return False

    def _from_community(self, from_id: int) -> bool:
        if not from_id or from_id <= 0:
            return True
        return from_id == -config.VK_GROUP_ID

    def should_reply(self, msg: dict[str, Any]) -> bool:
        peer_id = msg["peer_id"]
        from_id = msg["from_id"]
        text = msg["text"]
        payload = msg["payload"]

        if not peer_id:
            return False
        if msg["out"]:
            return False
        if msg["action"]:
            return False
        if not text and not payload:
            return False
        # Сообщение от имени сообщества: в ЛС всё равно отвечаем меню, не эхо.
        if self._from_community(int(from_id or 0)):
            return bool(peer_id) and not is_chat(int(peer_id))

        if not is_chat(peer_id):
            return True

        reply = msg["reply_message"]
        reply_from = _field(reply, "from_id") if reply else None
        if reply_from == -config.VK_GROUP_ID:
            return True
        return bool(mention_re().search(text))

    def on_message(self, event: Any) -> None:
        msg = extract_message(event)
        if not self.should_reply(msg):
            logger.info(
                "Пропуск сообщения peer_id=%s from_id=%s out=%s",
                msg.get("peer_id"),
                msg.get("from_id"),
                msg.get("out"),
            )
            return

        text = strip_mention(msg["text"]) or msg["text"]
        peer_id = int(msg["peer_id"])
        from_id = int(msg["from_id"] or 0)
        logger.info(
            "Сообщение peer_id=%s from_id=%s text=%r cmd=%s",
            peer_id,
            from_id,
            text[:80],
            msg["payload"].get("cmd"),
        )

        if self._from_community(from_id):
            if text.startswith("Сейчас сообщение пришло") or text.startswith("Здравствуйте!"):
                logger.info("Пропуск собственного исходящего сообщения сообщества")
                return
            logger.info("Входящее от имени сообщества — показываю меню, без эха текста")
            self.send(peer_id, f"{AS_COMMUNITY_HINT}\n\n{GREETING}", main_keyboard())
            self.seen_peers.add(peer_id)
            return

        first_contact = peer_id not in self.seen_peers
        if self.handle_menu(peer_id, text, msg["payload"]):
            self.seen_peers.add(peer_id)
            return

        if peer_id in self.awaiting_request:
            self.awaiting_request.discard(peer_id)
            self.seen_peers.add(peer_id)
            self.send(peer_id, REQUEST_THANKS, main_keyboard())
            return

        self.seen_peers.add(peer_id)
        if first_contact:
            self.show_menu(peer_id)
            return

        self.send(peer_id, UNKNOWN_TEXT, main_keyboard())

    def run(self) -> None:
        logger.info(
            "Бот «%s» запущен. Сообщество: https://vk.ru/club%s",
            config.STUDIO_NAME,
            config.VK_GROUP_ID,
        )
        while True:
            try:
                for event in self.longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        try:
                            self.on_message(event)
                        except Exception:
                            logger.exception("Ошибка обработки сообщения")
            except KeyboardInterrupt:
                logger.info("Остановка бота")
                raise
            except Exception:
                logger.exception("Сбой Long Poll, повтор через 3 секунды")
                time.sleep(3)
                self.longpoll = self._make_longpoll()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.ROOT_DIR / "bot.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    setup_logging()
    DetailingBot().run()


if __name__ == "__main__":
    main()
