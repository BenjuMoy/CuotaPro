from dataclasses import dataclass

from app.application import Application
from app.utils.logger import setup_logging


@dataclass
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: str = "yeti"


def main():
    """Entry point for the application."""
    setup_logging()
    app = Application(AppConfig())
    app.run()


if __name__ == "__main__":
    main()
