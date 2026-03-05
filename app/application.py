import logging
from pathlib import Path

from app.bootstrap.app_initializer import AppInitializer
from app.bootstrap.error_handler import GlobalErrorHandler
from app.bootstrap.tk_factory import TkAppFactory
from app.database.config import DatabaseConfig
from app.main_window import MainWindow
from app.utils.constantes import DATABASE_BACKUP_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, app_config):
        self.app_config = app_config
        self.db_config = DatabaseConfig(
            db_path=Path(DATABASE_PATH),
            backup_dir=Path(DATABASE_BACKUP_DIR),
        )
        self.main_service = None
        self.initializer = None
        self.main_window = None
        self.root = None

    def bootstrap(self):
        logger.info("Bootstrapping application")

        self.root = TkAppFactory.create_root(
            theme=self.app_config.theme,
            title=self.app_config.window_title,
        )

        GlobalErrorHandler(self.root).install()

        self.initializer = AppInitializer(self.db_config)

        self.main_service = self.initializer.initialize()
        self.main_window = MainWindow(self.root, self.main_service)

        logger.info("Application bootstrapped successfully")

    def run(self):
        self.bootstrap()

        try:
            self.root.mainloop()
        except Exception:
            logger.exception("Fatal error during runtime")
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down application")

        try:
            if self.main_service:
                self.main_service.create_backup()
        except Exception:
            logger.exception("Backup failed during shutdown")

        if self.initializer:
            self.initializer.shutdown()

        logger.info("Application shutdown complete")
