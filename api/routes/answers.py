from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, List

from database.db import submit_answer, get_answers
from api.deps import get_ws_manager
from api.ws import WSManager

router = APIRouter()

class AnswerBody(BaseModel):
    round_id: int
    text: str
    author_id: int

@router.post("/rooms/{room_id}/answers")
async def post_answer_api(room_id: int, body: AnswerBody, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    try:
        ans = await submit_answer(body.round_id, body.author_id, body.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws.broadcast(room_id, {"type": "answer_added", "payload": {"answer_id": ans["id"], "text": ans["text"]}})
    return {"answer_id": ans["id"]}

@router.get("/rooms/{room_id}/answers")
async def list_answers_api(room_id: int, round_id: int) -> List[Dict[str, Any]]:
    return await get_answers(round_id)
