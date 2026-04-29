import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGS_DIR = Path.home() / "CuotaPro" / "logs"
LOGS_PATH = LOGS_DIR / "app.log"


def setup_logging(level: int = logging.INFO) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()

    # Prevent duplicate handlers but still allow reconfiguration
    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOGS_PATH,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
