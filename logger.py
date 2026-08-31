import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging():

    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        filename=Path(LOG_DIR) / LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    for name in ["bornochinho", "uvicorn", "uvicorn.error"]:
        logger = logging.getLogger(name)
        logger.setLevel(LOG_LEVEL)
        logger.handlers = [handler]
        logger.propagate = False


def get_logger(name: str):

    return logging.getLogger(f"bornochinho.{name}")
