import asyncio, os, tempfile
import pytest
from database import db as dbmod

@pytest.mark.asyncio
async def test_answers_flow():
    with tempfile.TemporaryDirectory() as td:
        dbmod.set_db_path(os.path.join(td, "t.db"))
        await dbmod.ensure_initialized()
        u1 = await dbmod.get_or_create_user("2001", "Cat")
        u2 = await dbmod.get_or_create_user("2002", "Dog")
        room = await dbmod.create_room(u1["id"])
        await dbmod.join_room(room["code"], u2["id"])
        rd = await dbmod.set_question(room["id"], "Test question?")
        a1 = await dbmod.submit_answer(rd["id"], u2["id"], "Answer from Dog")
        with pytest.raises(ValueError):
            await dbmod.submit_answer(rd["id"], u2["id"], "Duplicate")
        ans = await dbmod.get_answers(rd["id"])
        assert len(ans) == 1
        assert ans[0]["revealed"] == 0
