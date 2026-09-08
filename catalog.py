from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    key: str
    title: str
    price: int
    short: str
    included: str
    for_whom: str
    duration: str
    notes: str


SERVICES: tuple[Service, ...] = (
    Service(
        key="interior",
        title="Химчистка салона",
        price=8_000,
        short="Освежаем салон: сиденья, потолок и пластик легкового автомобиля.",
        included=(
            "Химчистка сидений, потолка, пластиковых панелей и ковров. "
            "Удаляем пыль, пятна и запахи бытового характера."
        ),
        for_whom="Легковой автомобиль. Для SUV и коммерческого транспорта цена уточняется у менеджера.",
        duration="Обычно 4–8 часов в зависимости от загрязнения.",
        notes="Сильные загрязнения и застарелые пятна могут потребовать дополнительной обработки.",
    ),
    Service(
        key="polish",
        title="Полировка кузова",
        price=12_000,
        short="Одноэтапная полировка ЛКП — блеск и ровный вид кузова.",
        included=(
            "Мойка, оценка покрытия и одноэтапная полировка лакокрасочного покрытия "
            "легкового автомобиля. Снимаем лёгкие царапины и окисление, возвращаем блеск."
        ),
        for_whom="Легковой автомобиль с ЛКП в рабочем состоянии, без глубоких сколов.",
        duration="Обычно 1 рабочий день.",
        notes="Глубокие царапины до грунта полировка не убирает — это скажет мастер на осмотре.",
    ),
    Service(
        key="ceramic",
        title="Керамическое покрытие",
        price=25_000,
        short="Подготовка кузова и керамика в 1 слой для легкового автомобиля.",
        included=(
            "Подготовка поверхности (мойка, обезжиривание) и нанесение керамического "
            "покрытия в 1 слой. Защита от воды, грязи и ультрафиолета, более лёгкий уход."
        ),
        for_whom="Легковой автомобиль после полировки или с ровным ЛКП.",
        duration="Обычно 1–2 дня с учётом сушки слоя.",
        notes="Для максимального эффекта покрытие лучше наносить после полировки.",
    ),
)

PRICE_NOTE = (
    "Цены указаны для легковых автомобилей. "
    "Для SUV и коммерческого транспорта стоимость может быть выше — уточните у менеджера."
)

SERVICES_BY_KEY = {item.key: item for item in SERVICES}
SERVICES_BY_TITLE = {item.title.lower(): item for item in SERVICES}


def format_price(amount: int) -> str:
    return f"{amount:,} ₽".replace(",", " ")


def format_services() -> str:
    lines = [
        "Наши услуги — нажмите кнопку, чтобы открыть описание:",
        "",
    ]
    for item in SERVICES:
        lines.append(f"• {item.title} — {format_price(item.price)}")
        lines.append(f"  {item.short}")
        lines.append("")
    lines.append("Полная таблица цен — в разделе «Прайс-лист».")
    return "\n".join(lines).strip()


def format_price_list() -> str:
    lines = [
        "Прайс-лист (легковой автомобиль):",
        "",
    ]
    for item in SERVICES:
        lines.append(f"• {item.title} — {format_price(item.price)}")
        lines.append("")
    lines.append(PRICE_NOTE)
    return "\n".join(lines).strip()


def format_service(item: Service) -> str:
    return "\n".join(
        [
            f"{item.title}",
            f"Цена: {format_price(item.price)}",
            "",
            f"Что входит: {item.included}",
            "",
            f"Для кого: {item.for_whom}",
            f"Срок: {item.duration}",
            "",
            f"Важно: {item.notes}",
            "",
            PRICE_NOTE,
        ]
    )


def find_service(text: str) -> Service | None:
    normalized = " ".join(text.lower().split())
    if normalized in SERVICES_BY_TITLE:
        return SERVICES_BY_TITLE[normalized]
    for item in SERVICES:
        if item.title.lower() in normalized or item.key == normalized:
            return item
    return None
