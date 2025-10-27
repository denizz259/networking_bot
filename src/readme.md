# Networking Bot

Личный Telegram-бот для нетворкинга: категории (дизайнеры, инвесторы, и т.д.) и контакты внутри категорий.

## Локальный запуск (dev)

1. Создай `.env` на основе `.env.example` и впиши туда свой TELEGRAM_BOT_TOKEN.
2. Установи зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
