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
        self._config = AppConfig()
        self._db_config = DatabaseConfig()

        self._root: ttk.Window
        self._services: ApplicationService
        self._initializer: AppInitializer
        self.main_window: MainWindow

    def bootstrap(self):
        logger.info("Bootstrapping application")

        self._root = TkAppFactory.create_root(
            self._config.theme,
            self._config.window_title,
        )
        self._root.protocol("WM_DELETE_WINDOW", self.shutdown)

        GlobalErrorHandler(self._root).install()

        self._initializer = AppInitializer(self._db_config)

        self._services = self._initializer.initialize()
        self.main_window = MainWindow(self._root, self._services)

        logger.info("Application bootstrapped successfully")

    def run(self):
        try:
            self.bootstrap()
            self._root.mainloop()
        except Exception:
            logger.exception("Fatal error during runtime")
            raise
        finally:
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down application")

        try:
            if self._services:
                self._services.create_backup()
        except Exception:
            logger.exception("Backup failed during shutdown")

        if self._initializer:
            self._initializer.shutdown()

        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass

        logger.info("Application shutdown complete")
