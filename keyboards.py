from __future__ import annotations

import json

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from catalog import SERVICES

BTN_SERVICES = "Услуги"
BTN_PRICES = "Прайс-лист"
BTN_MANAGER = "Связаться с менеджером"
BTN_MENU = "Главное меню"
BTN_BACK = "Назад"
BTN_BACK_SERVICES = "Назад к услугам"


def _payload(**data: str) -> str:
    return json.dumps(data, ensure_ascii=False)


def main_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_SERVICES, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="services"))
    keyboard.add_button(BTN_PRICES, color=VkKeyboardColor.POSITIVE, payload=_payload(cmd="prices"))
    keyboard.add_line()
    keyboard.add_button(BTN_MANAGER, color=VkKeyboardColor.SECONDARY, payload=_payload(cmd="manager"))
    return keyboard.get_keyboard()


def services_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    for index, item in enumerate(SERVICES):
        if index:
            keyboard.add_line()
        keyboard.add_button(
            item.title,
            color=VkKeyboardColor.PRIMARY,
            payload=_payload(cmd="service", key=item.key),
        )
    keyboard.add_line()
    keyboard.add_button(BTN_PRICES, color=VkKeyboardColor.POSITIVE, payload=_payload(cmd="prices"))
    keyboard.add_button(BTN_MANAGER, color=VkKeyboardColor.SECONDARY, payload=_payload(cmd="manager"))
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="menu"))
    return keyboard.get_keyboard()


def service_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_BACK_SERVICES, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="services"))
    keyboard.add_line()
    keyboard.add_button(BTN_PRICES, color=VkKeyboardColor.POSITIVE, payload=_payload(cmd="prices"))
    keyboard.add_button(BTN_MANAGER, color=VkKeyboardColor.SECONDARY, payload=_payload(cmd="manager"))
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="menu"))
    return keyboard.get_keyboard()


def prices_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_SERVICES, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="services"))
    keyboard.add_button(BTN_MANAGER, color=VkKeyboardColor.SECONDARY, payload=_payload(cmd="manager"))
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="menu"))
    return keyboard.get_keyboard()


def manager_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(BTN_SERVICES, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="services"))
    keyboard.add_button(BTN_PRICES, color=VkKeyboardColor.POSITIVE, payload=_payload(cmd="prices"))
    keyboard.add_line()
    keyboard.add_button(BTN_MENU, color=VkKeyboardColor.PRIMARY, payload=_payload(cmd="menu"))
    return keyboard.get_keyboard()
