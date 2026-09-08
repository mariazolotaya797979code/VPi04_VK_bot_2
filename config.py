from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from http_setup import disable_env_proxy

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")
disable_env_proxy()


def _env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default if default is not None else "")
    value = (value or "").strip()
    if required and (not value or value.startswith("YOUR_")):
        raise SystemExit(
            f"Не задан {name}. Скопируйте .env.example в .env и вставьте ключи."
        )
    return value


def _parse_group_id(raw: str) -> int:
    value = (raw or "").strip()
    if not value:
        return 0
    lowered = value.lower()
    for prefix in (
        "https://vk.com/",
        "https://vk.ru/",
        "http://vk.com/",
        "http://vk.ru/",
        "vk.com/",
        "vk.ru/",
    ):
        if lowered.startswith(prefix):
            value = value[len(prefix) :]
            lowered = value.lower()
            break
    value = value.strip("/")
    lowered = value.lower()
    for prefix in ("club", "public", "event"):
        if lowered.startswith(prefix):
            value = value[len(prefix) :]
            break
    if value.startswith("-"):
        value = value[1:]
    if not value.isdigit():
        raise SystemExit(
            "VK_GROUP_ID должен быть числом или вида club123456. "
            f"Сейчас: {raw!r}"
        )
    return int(value)


VK_TOKEN = _env("VK_TOKEN", required=True)
VK_GROUP_ID = _parse_group_id(_env("VK_GROUP_ID", "0") or "0")
VK_API_VERSION = _env("VK_API_VERSION", "5.199")

STUDIO_NAME = _env("STUDIO_NAME", "Детейлинг-студия")
MANAGER_URL = _env("MANAGER_URL")
MANAGER_ID = _env("MANAGER_ID")
