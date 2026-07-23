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


DISCORD_TOKEN: str = _require_str("DISCORD_TOKEN")
PANEL_CHANNEL_ID: int = _require_int("PANEL_CHANNEL_ID")

_guild_id_raw = os.getenv("GUILD_ID")
GUILD_ID: int | None = int(_guild_id_raw) if _guild_id_raw else None

SOUNDS_DIR: str = os.getenv("SOUNDS_DIR", "sounds")
