from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict

from database.db import create_room, join_room, get_room_state
from api.deps import get_ws_manager
from api.ws import WSManager

router = APIRouter()

class JoinBody(BaseModel):
    room_code: str
    tg_user_id: str
    name: str

@router.post("/rooms")
async def create_room_api(data: JoinBody, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    """
    Creates room owned by provided user (user must exist client-side first).
    """
    from database.db import get_or_create_user
    user = await get_or_create_user(data.tg_user_id, data.name)
    room = await create_room(user["id"])
    # Owner joins already inside create_room
    return {"room_id": room["id"], "room_code": room["code"]}

@router.post("/rooms/join")
async def join_room_api(body: JoinBody, ws: WSManager = Depends(get_ws_manager)) -> Dict[str, Any]:
    from database.db import get_or_create_user
    user = await get_or_create_user(body.tg_user_id, body.name)
    try:
        result = await join_room(body.room_code, user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await ws.broadcast(result["room"]["id"], {"type": "player_joined", "payload": {"user_id": user["id"], "name": user["name"]}})
    return {
        "room_id": result["room"]["id"],
        "player_id": result["player"]["id"],
        "super_cards": result["player"]["super_cards"]
    }

@router.get("/rooms/{room_id}")
async def get_room_api(room_id: int) -> Dict[str, Any]:
    try:
        state = await get_room_state(room_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return state
