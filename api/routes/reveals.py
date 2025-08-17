from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict

from database.db import reveal_answer
from api.deps import get_ws_manager
from api.ws import WSManager

router = APIRouter()

class RevealBody(BaseModel):
    round_id: int
    answer_id: int
    actor_id: int

@router.post("/rooms/{room_id}/reveal")
async def reveal_api(room_id: int, body: RevealBody, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    try:
        result = await reveal_answer(body.round_id, body.answer_id, body.actor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws.broadcast(room_id, {"type": "answer_revealed", "payload": result})
    return result
