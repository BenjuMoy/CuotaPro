import logging
from dataclasses import dataclass

import ttkbootstrap as ttk

from app.bootstrap.app_initializer import AppInitializer
from app.bootstrap.error_handler import GlobalErrorHandler
from app.bootstrap.tk_factory import TkAppFactory
from app.database.config import DatabaseConfig
from app.services.application_service import ApplicationService
from app.views.main_window import MainWindow

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: str = "yeti"


class Application:
    def __init__(self):
        self._config = AppConfig()
        self._db_config = DatabaseConfig()

    def bootstrap(self):
        logger.info("Bootstrapping application")

        root = TkAppFactory.create_root(self._config.theme, self._config.window_title)
        GlobalErrorHandler(root).install()
        initializer = AppInitializer(self._db_config)
        services = initializer.initialize()
        main_window = MainWindow(root, services)

        logger.info("Application bootstrapped successfully")

        return root, initializer, services, main_window

    def run(self) -> int:
        root, initializer, services, _ = self.bootstrap()
        try:
            root.mainloop()

        except Exception:
            logger.exception("Fatal error during runtime")
            raise

        finally:
            self.shutdown(root, initializer, services)

        return 0

    def shutdown(
        self,
        root: ttk.Window,
        initializer: AppInitializer,
        services: ApplicationService,
    ):
        logger.info("Shutting down application")

        try:
            services.create_backup()
        except Exception:
            logger.exception("Backup failed during shutdown")

        try:
            root.destroy()
        except Exception:
            pass

        logger.info("Application shutdown complete")
