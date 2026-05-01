import logging

from bootstrap.bootstrap import ApplicationBuilder
from infrastructure.logging.logger import setup_logging


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting application")
        app = ApplicationBuilder().build()
        return app.run()

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        return 130

    except Exception:
        logger.exception("Fatal error during startup")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
