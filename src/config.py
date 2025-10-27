# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные из .env если запускаем локально
load_dotenv()

BOT_TOKEN = os.getenv("TG_API")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db.sqlite")

if BOT_TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")
