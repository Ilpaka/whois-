from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

from database.db import get_or_create_user, get_user_by_id

router = APIRouter()

class UserBody(BaseModel):
    tg_user_id: str
    name: str

@router.post("/users")
async def upsert_user_api(body: UserBody) -> Dict[str, Any]:
    user = await get_or_create_user(body.tg_user_id, body.name)
    return {"user_id": user["id"], "name": user["name"]}

@router.get("/users/{user_id}")
async def get_user_api(user_id: int) -> Dict[str, Any]:
    u = await get_user_by_id(user_id)
    if not u:
        return {"exists": False}
    return {"exists": True, "user_id": u["id"], "name": u["name"]}
