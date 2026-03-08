import logging
from dataclasses import dataclass
from pathlib import Path

import ttkbootstrap as ttk

from app.bootstrap.app_initializer import AppInitializer
from app.bootstrap.error_handler import GlobalErrorHandler
from app.bootstrap.tk_factory import TkAppFactory
from app.database.config import DatabaseConfig
from app.main_window import MainWindow
from app.services.application_service import ApplicationService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: str = "yeti"


class Application:
    def __init__(self):
        self.app_config = AppConfig()
        self.db_config = DatabaseConfig()
        self.main_service: ApplicationService | None = None
        self.initializer: AppInitializer | None = None
        self.main_window: MainWindow | None = None
        self.root: ttk.Window | None = None

    def bootstrap(self):
        logger.info("Bootstrapping application")

        self.root = TkAppFactory.create_root(
            self.app_config.theme,
            self.app_config.window_title,
        )

        GlobalErrorHandler(self.root).install()

        self.initializer = AppInitializer(self.db_config)

        self.main_service = self.initializer.initialize()
        self.main_window = MainWindow(self.root, self.main_service)

        logger.info("Application bootstrapped successfully")

    def run(self):
        try:
            self.bootstrap()
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
