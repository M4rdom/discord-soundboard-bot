"""Loads and validates the bot configuration from environment variables (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()


def _require_str(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable '{name}' in the .env file")
    return value


def _require_int(name: str) -> int:
    value = _require_str(name)
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"'{name}' must be a valid numeric ID") from exc


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"'{name}' must be a valid integer") from exc
    if parsed < 1:
        raise RuntimeError(f"'{name}' must be at least 1")
    return parsed


DISCORD_TOKEN: str = _require_str("DISCORD_TOKEN")
PANEL_CHANNEL_ID: int = _require_int("PANEL_CHANNEL_ID")

_guild_id_raw = os.getenv("GUILD_ID")
GUILD_ID: int | None = int(_guild_id_raw) if _guild_id_raw else None

SOUNDS_DIR: str = os.getenv("SOUNDS_DIR", "sounds")

# How many messages the panel can spread across to fit more than 4 categories
# (Discord's per-message Select Menu limit). See sound_library.MAX_CATEGORIES_PER_MESSAGE.
PANEL_MAX_MESSAGES: int = _positive_int("PANEL_MAX_MESSAGES", default=3)
