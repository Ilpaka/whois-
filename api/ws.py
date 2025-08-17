from __future__ import annotations
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class WSManager:
    def __init__(self):
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, room_id: int, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(room_id, set()).add(ws)

    def _discard(self, room_id: int, ws: WebSocket):
        try:
            self.rooms.get(room_id, set()).discard(ws)
            if not self.rooms.get(room_id):
                self.rooms.pop(room_id, None)
        except Exception:
            pass

    async def disconnect(self, room_id: int, ws: WebSocket):
        self._discard(room_id, ws)

    async def broadcast(self, room_id: int, message: dict):
        dead = []
        for ws in list(self.rooms.get(room_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._discard(room_id, ws)

@router.websocket("/ws/rooms/{room_id}")
async def ws_room(websocket: WebSocket, room_id: int):
    mgr: WSManager = websocket.app.state.ws_manager
    await mgr.connect(room_id, websocket)
    try:
        while True:
            # Keepalive / echo ping
            await websocket.receive_text()
    except WebSocketDisconnect:
        await mgr.disconnect(room_id, websocket)
