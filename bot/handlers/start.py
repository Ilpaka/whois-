from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from bot.keyboards import main_menu_kb

router = Router()

@router.message(CommandStart())
async def start_cmd(msg: Message):
    await msg.answer(
        "Привет! Это мини-игра <b>Who Said That?</b>\n"
        "Открой мини-приложение, создай комнату и зови друзей!",
        reply_markup=main_menu_kb()
    )

@router.callback_query(F.data == "back_to_menu")
async def back_menu(cb: CallbackQuery):
    await cb.message.edit_text("Главное меню", reply_markup=main_menu_kb())
    await cb.answer()
