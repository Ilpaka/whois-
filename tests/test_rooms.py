import asyncio, os, tempfile
import pytest
from database import db as dbmod

@pytest.mark.asyncio
async def test_create_and_join_room():
    with tempfile.TemporaryDirectory() as td:
        dbpath = os.path.join(td, "t.db")
        dbmod.set_db_path(dbpath)
        await dbmod.ensure_initialized()

        u1 = await dbmod.get_or_create_user("1001", "Alice")
        u2 = await dbmod.get_or_create_user("1002", "Bob")
        room = await dbmod.create_room(u1["id"])

        state = await dbmod.get_room_state(room["id"])
        assert state["room_code"] == room["code"]
        assert state["players"][0]["user_id"] == u1["id"]

        j = await dbmod.join_room(room["code"], u2["id"])
        assert j["player"]["super_cards"] == 3
