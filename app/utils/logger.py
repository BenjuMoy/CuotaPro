import logging
from logging.handlers import RotatingFileHandler

from app.utils.constantes import LOGS_DIR, LOGS_PATH

LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOGS_PATH,
        maxBytes=1_000_000,  # 1MB
        backupCount=5,
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
