from __future__ import annotations
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("ping"))
async def ping(msg: Message):
    await msg.answer("pong")
