import logging
from dataclasses import dataclass

import ttkbootstrap as ttk
from ttkbootstrap.window import Window

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


class Application:
    def __init__(self, config, db_config: DatabaseConfig):
        self.config = config
        self.db_config = db_config

    def bootstrap(self):
        logger.info("Bootstrapping application")

        root = self._create_ui()
        services = self._create_services()
        main_window = MainWindow(root, services)

        logger.info("Application bootstrapped successfully")

        return AppContext(root, services, main_window)

    def _create_ui(self) -> Window:
        root = TkAppFactory.create_root(self.config.theme, self.config.window_title)
        GlobalErrorHandler(root).install()
        return root

    def _create_services(self) -> ApplicationService:
        initializer = AppInitializer(self.db_config)
        container = initializer.initialize()
        return ApplicationService(container)

    def run(self) -> int:
        context = None
        try:
            context = self.bootstrap()
            context.root.mainloop()

        except Exception:
            logger.exception("Fatal error during runtime")
            raise

        finally:
            if context:
                self.shutdown(context)

        return 0

    def shutdown(self, context: AppContext) -> None:
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
