from __future__ import annotations
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import httpx

from bot.keyboards import main_menu_kb
from config import get_config

router = Router()

class JoinStates(StatesGroup):
    waiting_code = State()

@router.callback_query(F.data == "create_room")
async def cb_create_room(cb: CallbackQuery):
    cfg = get_config()
    # Create user in API (use Telegram info)
    name = cb.from_user.full_name
    tg_id = str(cb.from_user.id)
    async with httpx.AsyncClient() as cli:
        await cli.post(f"{cfg.WEBAPP_URL}/users", json={"tg_user_id": tg_id, "name": name})
        r = await cli.post(f"{cfg.WEBAPP_URL}/rooms", json={"room_code":"", "tg_user_id": tg_id, "name": name})
        r.raise_for_status()
        data = r.json()
    await cb.message.answer(
        f"Комната создана! Код: <code>{data['room_code']}</code>\nОткрой мини-игру и отправь код друзьям.",
        reply_markup=main_menu_kb()
    )
    await cb.answer()

@router.callback_query(F.data == "join_room")
async def cb_join_room(cb: CallbackQuery, state: FSMContext):
    await state.set_state(JoinStates.waiting_code)
    await cb.message.answer("Введите код комнаты (6 символов, A-Z/0-9):")
    await cb.answer()

@router.message(JoinStates.waiting_code)
async def process_code(msg: Message, state: FSMContext):
    code = (msg.text or "").strip().upper()
    if len(code) != 6:
        await msg.answer("Код должен быть из 6 символов. Попробуйте снова или нажмите /start.")
        return
    cfg = get_config()
    async with httpx.AsyncClient() as cli:
        # upsert user
        await cli.post(f"{cfg.WEBAPP_URL}/users", json={"tg_user_id": str(msg.from_user.id), "name": msg.from_user.full_name})
        r = await cli.post(f"{cfg.WEBAPP_URL}/rooms/join", json={"room_code": code, "tg_user_id": str(msg.from_user.id), "name": msg.from_user.full_name})
        if r.status_code != 200:
            await msg.answer(f"Не удалось войти: {r.json().get('detail')}")
            await state.clear()
            return
    await msg.answer("Вы в комнате! Откройте мини-игру кнопкой ниже.", reply_markup=main_menu_kb())
    await state.clear()
