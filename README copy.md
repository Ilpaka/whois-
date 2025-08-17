# Who Said That? — Telegram Mini-App

Игра для компаний: подключай друзей в комнату, отвечайте анонимно на общий вопрос, обсуждайте, «вскрывайте» авторов с помощью супер-карточек.

## Стек
- Python 3.11+
- aiogram v3 (бот, Long Polling)
- FastAPI (REST + WebSocket)
- SQLite (через `aiosqlite`), без ORM
- Чистый HTML/CSS/JS для WebApp

## Установка и запуск
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Заполните config.json (BOT_TOKEN, WEBAPP_URL, DEV_MODE)
# (или используйте переменные окружения, см. .env.example)

# Инициализация БД (автоматически выполняется при старте API),
# но можно руками:
python database/db.py --init

# Запуск API (порт 8000, также раздаёт webapp/ как статику)
python run_api.py

# В другом терминале запустите бота
python run_bot.py
```

Откройте бота в Telegram → `/start` → кнопка **Открыть мини-игру**.
WebApp откроется по адресу из `WEBAPP_URL` (по умолчанию `http://localhost:8000`).

## Архитектура
- `run_api.py` — FastAPI приложение, эндпоинты в `api/routes/*`, WS — `api/ws.py`.
- `database/db.py` — асинхронные функции доступа к SQLite, транзакции и инварианты.
- `bot/*` — aiogram v3: роутеры, клавиатуры, middlewares, обработчики.
- `webapp/*` — фронтенд мини-приложения с анимациями, адаптивом и WebSocket.

## Тесты
```bash
pytest -q
```

## Prod заметки
- Для валидации Telegram initData включите проверку хэша (см. `webapp/scripts/main.js` — отмечено комментарием).
- Если планируется масштабирование по процессам — вынесите WS-хаб во внешний брокер (Redis) и/или используйте push-сервис.
- Добавьте rate-limit и анти-флуд в API/бот.
