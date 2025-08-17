from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import get_config

def main_menu_kb() -> InlineKeyboardMarkup:
    cfg = get_config()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть мини-игру", web_app=WebAppInfo(url=cfg.WEBAPP_URL))],
        [InlineKeyboardButton(text="Создать комнату", callback_data="create_room")],
        [InlineKeyboardButton(text="Присоединиться по коду", callback_data="join_room")]
    ])
