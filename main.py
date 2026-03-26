from dataclasses import dataclass

from app.application import Application
from app.database.config import DatabaseConfig
from app.utils.logger import setup_logging


@dataclass(frozen=True)
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: str = "yeti"


def main() -> int:
    """Entry point for the application."""
    setup_logging()

    app = Application(config=AppConfig(), db_config=DatabaseConfig())

    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
