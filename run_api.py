# run_api.py
from __future__ import annotations
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_config
from database.db import ensure_initialized, set_db_path
from api.routes.rooms import router as rooms_router
from api.routes.prompts import router as prompts_router
from api.routes.answers import router as answers_router
from api.routes.reveals import router as reveals_router
from api.routes.users import router as users_router
from api.ws import WSManager, router as ws_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

cfg = get_config()
set_db_path(cfg.DB_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_initialized()
    logging.info("API started at %s", cfg.WEBAPP_URL)
    yield

app = FastAPI(title="Who Said That? API", lifespan=lifespan)

# CORS (в проде сузьте домены)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WS менеджер в state
app.state.ws_manager = WSManager()

# СНАЧАЛА подключаем API/WS роуты…
app.include_router(rooms_router, prefix="")
app.include_router(prompts_router, prefix="")
app.include_router(answers_router, prefix="")
app.include_router(reveals_router, prefix="")
app.include_router(users_router, prefix="")
app.include_router(ws_router, prefix="")

# …и ТОЛЬКО ПОТОМ монтируем статику на корень
web_dir = Path(__file__).resolve().parent / "webapp"
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="webapp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run_api:app", host="0.0.0.0", port=8000, reload=False)
