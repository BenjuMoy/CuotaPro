from app.application import Application
from app.utils.logger import setup_logging


def main():
    """Entry point for the application."""
    setup_logging()
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
