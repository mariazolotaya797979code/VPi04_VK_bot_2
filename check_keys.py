from __future__ import annotations

import vk_api
from vk_api.exceptions import ApiError

import config
from http_setup import no_proxy_session


def _first_group(response: object) -> dict:
    if isinstance(response, dict):
        items = response.get("groups") or response.get("items") or []
    else:
        items = response
    if not items:
        raise RuntimeError(f"VK не вернул сообщество: {response!r}")
    return items[0]


def main() -> None:
    session = vk_api.VkApi(token=config.VK_TOKEN, api_version=config.VK_API_VERSION)
    no_proxy_session(session.http)
    vk = session.get_api()

    try:
        group = _first_group(vk.groups.getById(group_ids=str(config.VK_GROUP_ID)))
        name = group.get("name", "?")
        real_id = int(group.get("id") or 0)
        print(f"[OK] VK: сообщество «{name}» (id={real_id})")
        if real_id and real_id != config.VK_GROUP_ID:
            print(
                f"[WARN] VK_GROUP_ID в .env={config.VK_GROUP_ID}, "
                f"а токен относится к группе {real_id}"
            )
    except ApiError as exc:
        print(f"[FAIL] VK groups.getById: {exc}")
        raise SystemExit(1) from exc

    try:
        vk.groups.setLongPollSettings(
            group_id=config.VK_GROUP_ID,
            enabled=1,
            api_version=config.VK_API_VERSION,
            message_new=1,
        )
        print("[OK] VK: Long Poll включён (message_new=1)")
    except ApiError as exc:
        print(f"[WARN] Не удалось включить Long Poll через API: {exc}")

    try:
        vk.groups.getLongPollServer(group_id=config.VK_GROUP_ID)
        print("[OK] VK: Long Poll сервер доступен")
    except ApiError as exc:
        print(f"[FAIL] VK Long Poll: {exc}")
        raise SystemExit(1) from exc

    print("Всё готово. Запускайте: python bot.py")


if __name__ == "__main__":
    main()
