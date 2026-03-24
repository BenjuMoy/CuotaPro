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


@dataclass
class AppContext:
    root: ttk.Window
    services: ApplicationService
    main_window: MainWindow


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
        app_service = ApplicationService(AppInitializer(self._db_config).initialize())
        main_window = MainWindow(root, app_service)

        logger.info("Application bootstrapped successfully")

        return AppContext(root, app_service, main_window)

    def run(self) -> int:
        context = self.bootstrap()
        try:
            context.root.mainloop()

        except Exception:
            logger.exception("Fatal error during runtime")
            raise

        finally:
            self.shutdown(context)

        return 0

    def shutdown(self, context: AppContext):
        logger.info("Shutting down application")

        try:
            context.services.create_backup()
        except Exception:
            logger.exception("Backup failed during shutdown")

        try:
            context.root.destroy()
        except Exception:
            logger.exception("Failed to destroy root window")

        logger.info("Application shutdown complete")
