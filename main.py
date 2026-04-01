from app.application import Application
from app.database.config import DatabaseConfig
from app.models.config import AppConfig
from app.utils.logger import setup_logging


def main() -> int:
    """Entry point for the application."""
    setup_logging()

    app = Application(config=AppConfig(), db_config=DatabaseConfig())

    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
