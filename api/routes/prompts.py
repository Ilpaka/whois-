from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict

from database.db import set_question, get_current_question, close_round
from api.deps import get_ws_manager
from api.ws import WSManager

router = APIRouter()

class QuestionBody(BaseModel):
    text: str

@router.post("/rooms/{room_id}/question")
async def set_question_api(room_id: int, body: QuestionBody, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    try:
        rd = await set_question(room_id, body.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws.broadcast(room_id, {"type": "question_set", "payload": {"round_id": rd["id"], "text": rd["question"], "status": rd["status"]}})
    return {"round_id": rd["id"], "text": rd["question"], "status": rd["status"]}

@router.get("/rooms/{room_id}/question")
async def get_question_api(room_id: int) -> Dict[str, Any]:
    rd = await get_current_question(room_id)
    if not rd:
        return {"round_id": None, "text": None, "status": "idle"}
    return {"round_id": rd["id"], "text": rd["question"], "status": rd["status"]}

@router.post("/rooms/{room_id}/round/close")
async def close_round_api(room_id: int, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    await close_round(room_id)
    await ws.broadcast(room_id, {"type": "round_closed", "payload": {}})
    return {"ok": True}
