from __future__ import annotations
"""
Async DB helpers using aiosqlite, with invariants and transactions.
"""
import asyncio
import random
import string
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite
from config import PROJECT_ROOT

_DB_PATH = str(PROJECT_ROOT / "database" / "miniapp.db")
_SCHEMA_PATH = str(PROJECT_ROOT / "database" / "schema.sql")

def set_db_path(path: str) -> None:
    global _DB_PATH
    _DB_PATH = path

async def ensure_initialized() -> None:
    """Create tables if not exists by executing schema.sql."""
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB_PATH) as db:
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            await db.executescript(f.read())
        await db.commit()

def _code(n: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(n))

# ---------------- Users -----------------

async def get_or_create_user(tg_user_id: str, name: str) -> Dict[str, Any]:
    await ensure_initialized()
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE tg_user_id=?", (tg_user_id,))
        row = await cur.fetchone()
        if row:
            # Update name if changed
            if name and row["name"] != name:
                await db.execute("UPDATE users SET name=? WHERE id=?", (name, row["id"]))
                await db.commit()
                row = dict(row)
                row["name"] = name
                return row
            return dict(row)
        await db.execute("INSERT INTO users (tg_user_id, name) VALUES (?,?)", (tg_user_id, name or f"User{tg_user_id}"))
        await db.commit()
        cur = await db.execute("SELECT * FROM users WHERE tg_user_id=?", (tg_user_id,))
        return dict(await cur.fetchone())

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

# ---------------- Rooms -----------------

async def create_room(owner_user_id: int) -> Dict[str, Any]:
    await ensure_initialized()
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Generate unique code
        for _ in range(20):
            code = _code(6)
            cur = await db.execute("SELECT id FROM rooms WHERE code=?", (code,))
            if not await cur.fetchone():
                break
        else:
            raise RuntimeError("Не удалось сгенерировать уникальный код комнаты")
        await db.execute("INSERT INTO rooms (code, owner_user_id, status) VALUES (?,?, 'active')", (code, owner_user_id))
        await db.commit()
        cur = await db.execute("SELECT * FROM rooms WHERE code=?", (code,))
        room = dict(await cur.fetchone())
        # Owner auto-joins with 3 super-cards
        await db.execute(
            "INSERT OR IGNORE INTO room_players (room_id, user_id, super_cards) VALUES (?,?,3)",
            (room["id"], owner_user_id),
        )
        await db.commit()
        return room

async def get_room_by_code(room_code: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM rooms WHERE code=?", (room_code,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def get_room_by_id(room_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM rooms WHERE id=?", (room_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def join_room(room_code: str, user_id: int) -> Dict[str, Any]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM rooms WHERE code=?", (room_code,))
        room = await cur.fetchone()
        if not room:
            raise ValueError("Комната не найдена")
        if room["status"] != "active":
            raise ValueError("Комната закрыта")
        await db.execute(
            "INSERT OR IGNORE INTO room_players (room_id, user_id, super_cards) VALUES (?,?,3)",
            (room["id"], user_id),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM room_players WHERE room_id=? AND user_id=?", (room["id"], user_id))
        rp = dict(await cur.fetchone())
        return {"room": dict(room), "player": rp}

async def get_room_state(room_id: int) -> Dict[str, Any]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM rooms WHERE id=?", (room_id,))
        room = await cur.fetchone()
        if not room:
            raise ValueError("Комната не найдена")
        cur = await db.execute("""
            SELECT rp.id as player_id, u.id as user_id, u.name, rp.super_cards
            FROM room_players rp JOIN users u ON u.id = rp.user_id
            WHERE rp.room_id=?
            ORDER BY rp.joined_at ASC
        """, (room_id,))
        players = [dict(r) for r in await cur.fetchall()]
        # current round (last row by created_at)
        cur = await db.execute("""
            SELECT id, question, status, created_at
            FROM rounds WHERE room_id=?
            ORDER BY id DESC LIMIT 1
        """, (room_id,))
        current_round = await cur.fetchone()
        return {
            "room_id": room["id"],
            "room_code": room["code"],
            "status": room["status"],
            "players": players,
            "current_round": dict(current_round) if current_round else None
        }

# ---------------- Rounds & Prompts -----------------

async def set_question(room_id: int, text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text or len(text) > 200:
        raise ValueError("Вопрос пустой или слишком длинный (≤200)")
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Close previous collecting rounds (move to discussion)
        await db.execute("UPDATE rounds SET status='discussion' WHERE room_id=? AND status='collecting'", (room_id,))
        await db.execute("INSERT INTO rounds (room_id, question, status) VALUES (?,?, 'collecting')", (room_id, text))
        await db.commit()
        cur = await db.execute("SELECT * FROM rounds WHERE room_id=? ORDER BY id DESC LIMIT 1", (room_id,))
        return dict(await cur.fetchone())

async def get_current_question(room_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM rounds WHERE room_id=? ORDER BY id DESC LIMIT 1", (room_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

async def close_round(room_id: int) -> None:
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute("UPDATE rounds SET status='discussion' WHERE room_id=? AND status='collecting'", (room_id,))
        await db.commit()

# ---------------- Answers -----------------

async def submit_answer(round_id: int, user_id: int, text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text or len(text) > 300:
        raise ValueError("Ответ пустой или слишком длинный (≤300)")
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Ensure round exists and collecting
        cur = await db.execute("SELECT * FROM rounds WHERE id=?", (round_id,))
        rd = await cur.fetchone()
        if not rd:
            raise ValueError("Раунд не найден")
        if rd["status"] != "collecting":
            raise ValueError("Сбор ответов завершён")
        try:
            await db.execute("INSERT INTO answers (round_id, user_id, text) VALUES (?,?,?)", (round_id, user_id, text))
            await db.commit()
        except aiosqlite.IntegrityError:
            raise ValueError("Вы уже отправили ответ в этом раунде")
        cur = await db.execute("SELECT * FROM answers WHERE round_id=? AND user_id=?", (round_id, user_id))
        return dict(await cur.fetchone())

async def get_answers(round_id: int) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("""
            SELECT a.id as answer_id, a.text, a.revealed,
                   CASE WHEN a.revealed=1 THEN u.name ELSE NULL END as author_display
            FROM answers a JOIN users u ON u.id = a.user_id
            WHERE a.round_id=?
            ORDER BY a.id ASC
        """, (round_id,))
        return [dict(r) for r in await cur.fetchall()]

# ---------------- Reveals -----------------

async def reveal_answer(round_id: int, answer_id: int, actor_user_id: int) -> Dict[str, Any]:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("BEGIN"):
            # Load answer & round & room
            cur = await db.execute("SELECT * FROM answers WHERE id=? AND round_id=?", (answer_id, round_id))
            ans = await cur.fetchone()
            if not ans:
                raise ValueError("Ответ не найден")
            if ans["revealed"] == 1:
                raise ValueError("Этот ответ уже раскрыт")
            cur = await db.execute("SELECT * FROM rounds WHERE id=?", (round_id,))
            rd = await cur.fetchone()
            if not rd:
                raise ValueError("Раунд не найден")
            # Author cannot reveal own answer
            if ans["user_id"] == actor_user_id:
                raise ValueError("Нельзя раскрыть свой собственный ответ")
            # Get room_id
            room_id = rd["room_id"]
            # Find actor in room and decrement a super-card
            cur = await db.execute("""
                SELECT rp.id, rp.super_cards FROM room_players rp
                WHERE rp.room_id=? AND rp.user_id=?
            """, (room_id, actor_user_id))
            rp = await cur.fetchone()
            if not rp:
                raise ValueError("Вы не являетесь игроком этой комнаты")
            if rp["super_cards"] <= 0:
                raise ValueError("У вас нет супер-карт")
            await db.execute("UPDATE room_players SET super_cards=super_cards-1 WHERE id=? AND super_cards>0", (rp["id"],))
            # Mark answer as revealed
            await db.execute("UPDATE answers SET revealed=1, revealed_by_user_id=? WHERE id=?", (actor_user_id, answer_id))
            await db.commit()

        # fetch display name
        cur = await db.execute("""
            SELECT a.id as answer_id, u.name as author_display
            FROM answers a JOIN users u ON u.id = a.user_id
            WHERE a.id=?
        """, (answer_id,))
        row = await cur.fetchone()
        return dict(row)

# --------------- CLI -----------------

if __name__ == "__main__":
    import argparse, os
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Initialize DB schema")
    parser.add_argument("--db", type=str, default=_DB_PATH, help="Path to DB file")
    args = parser.parse_args()
    set_db_path(args.db)
    if args.init:
        asyncio.run(ensure_initialized())
        print(f"DB initialized at {args.db}")
