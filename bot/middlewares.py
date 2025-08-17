from __future__ import annotations
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

logger = logging.getLogger(__name__)

class RedactingLoggingMiddleware(BaseMiddleware):
    """Log updates without leaking secrets."""
    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        try:
            logger.debug("Update type: %s", event.event_type if hasattr(event, "event_type") else type(event))
        except Exception:
            pass
        return await handler(event, data)
