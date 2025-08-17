"""
Configuration loader for the mini-app.
Reads config.json from project root. Falls back to environment variables.
Raises a clear error if config.json is missing and env vars not set.
"""
from __future__ import annotations
import json, os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    WEBAPP_URL: str
    DEV_MODE: bool
    DB_PATH: str

_cached: Config | None = None

def load_json_config() -> dict:
    cfg_path = PROJECT_ROOT / "config.json"
    if not cfg_path.exists():
        # Try env as a fallback
        env_bot = os.environ.get("BOT_TOKEN")
        env_url = os.environ.get("WEBAPP_URL")
        env_dev = os.environ.get("DEV_MODE")
        if env_bot and env_url:
            return {
                "BOT_TOKEN": env_bot,
                "WEBAPP_URL": env_url,
                "DEV_MODE": (str(env_dev).lower() in {"1","true","yes"}),
                "DB_PATH": os.environ.get("DB_PATH", str(PROJECT_ROOT / "database" / "miniapp.db"))
            }
        raise FileNotFoundError(
            "Файл config.json не найден. Создайте его в корне проекта и укажите BOT_TOKEN, WEBAPP_URL, DEV_MODE. "
            "Либо задайте переменные окружения BOT_TOKEN, WEBAPP_URL, DEV_MODE."
        )
    with cfg_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def get_config() -> Config:
    global _cached
    if _cached:
        return _cached
    data = load_json_config()
    bot = data.get("BOT_TOKEN") or os.environ.get("BOT_TOKEN")
    url = data.get("WEBAPP_URL") or os.environ.get("WEBAPP_URL")
    dev = data.get("DEV_MODE", False)
    dbp = data.get("DB_PATH") or os.environ.get("DB_PATH") or str(PROJECT_ROOT / "database" / "miniapp.db")
    if not bot or "PASTE_TELEGRAM_BOT_TOKEN_HERE" in bot:
        raise RuntimeError("BOT_TOKEN не задан. Укажите корректный токен в config.json или переменной окружения.")
    if not url:
        raise RuntimeError("WEBAPP_URL не задан. Укажите адрес WebApp (например http://localhost:8000).")
    _cached = Config(BOT_TOKEN=bot, WEBAPP_URL=url, DEV_MODE=bool(dev), DB_PATH=dbp)
    return _cached
