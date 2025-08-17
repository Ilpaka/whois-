import asyncio, os, tempfile
import pytest
from database import db as dbmod

@pytest.mark.asyncio
async def test_reveal_spends_supercard_and_prohibits_double():
    with tempfile.TemporaryDirectory() as td:
        dbmod.set_db_path(os.path.join(td, "t.db"))
        await dbmod.ensure_initialized()
        u1 = await dbmod.get_or_create_user("3001", "Alice")
        u2 = await dbmod.get_or_create_user("3002", "Bob")
        room = await dbmod.create_room(u1["id"])
        await dbmod.join_room(room["code"], u2["id"])
        rd = await dbmod.set_question(room["id"], "Q?")
        a = await dbmod.submit_answer(rd["id"], u1["id"], "Alice's text")
        # Bob reveals Alice
        res = await dbmod.reveal_answer(rd["id"], a["id"], u2["id"])
        assert "author_display" in res
        # Double reveal not allowed
        with pytest.raises(ValueError):
            await dbmod.reveal_answer(rd["id"], a["id"], u2["id"])
        # Self-reveal not allowed
        a2 = await dbmod.submit_answer(rd["id"], u2["id"], "Bob's text")
        with pytest.raises(ValueError):
            await dbmod.reveal_answer(rd["id"], a2["id"], u2["id"])
