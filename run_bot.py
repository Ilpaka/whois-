from __future__ import annotations
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import get_config
from bot.handlers.start import router as start_router
from bot.handlers.rooms import router as rooms_router
from bot.handlers.admin import router as admin_router
from bot.middlewares import RedactingLoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

def redact_token(record: logging.LogRecord) -> None:
    # Ensure BOT token never leaks
    cfg = None
    try:
        cfg = get_config()
    except Exception:
        return
    if cfg and isinstance(record.msg, str) and cfg.BOT_TOKEN in record.msg:
        record.msg = record.msg.replace(cfg.BOT_TOKEN, "***TOKEN***")

class TokenRedactor(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        redact_token(record)
        return True

for name in ["aiogram", "httpx", "asyncio", "uvicorn", "uvicorn.error"]:
    logging.getLogger(name).addFilter(TokenRedactor())

async def main():
    cfg = get_config()
    bot = Bot(token=cfg.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.update.middleware(RedactingLoggingMiddleware())

    dp.include_router(start_router)
    dp.include_router(rooms_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
