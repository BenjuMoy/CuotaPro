from app.application import Application
from app.utils.logger import setup_logging


def main() -> int:
    """Entry point for the application."""
    setup_logging()

    app = Application()
    app.run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
