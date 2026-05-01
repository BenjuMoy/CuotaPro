import logging

import ttkbootstrap as ttk

from bootstrap.containers import ServiceContainer
from bootstrap.database import DatabaseInitializer
from bootstrap.services import ServiceFactory
from bootstrap.ui import UIFactory

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, root: ttk.Window, services: ServiceContainer):
        self.root = root
        self.services = services

    def run(self) -> int:
        try:
            self.root.mainloop()
            return 0

        finally:
            self.shutdown()

    def shutdown(self) -> None:
        logger.info("Shutting down application")

        try:
            self.services.maintenance.create_backup()
        except Exception:
            logger.exception("Backup failed")


class ApplicationBuilder:
    @staticmethod
    def build() -> Application:
        db_bundle = DatabaseInitializer().init()
        services = ServiceFactory().create(db_bundle)
        root = UIFactory().create(services)

        return Application(root, services)
