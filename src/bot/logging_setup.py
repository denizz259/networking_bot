import logging
import os
from pythonjsonlogger import jsonlogger


def configure_logging() -> logging.Logger:
    """Configure root logger with JSON formatter."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler()

    fmt = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)s"
    )
    handler.setFormatter(fmt)

    # Чтобы не плодить хендлеры при повторной инициализации
    logger.handlers = []
    logger.addHandler(handler)

    # Немного приглушим болтливые библиотеки, если они есть
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger
