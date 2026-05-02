import logging

import ttkbootstrap as ttk

from bootstrap.containers import ServiceContainer
from ui.main_window import MainWindow
from ui.tk.error_handler import ErrorHandlerInstaller
from ui.tk.tk_factory import TKRootFactory

logger = logging.getLogger(__name__)


class UIFactory:
    def create(self, services: ServiceContainer) -> ttk.Window:
        root = TKRootFactory().create_root()

        ErrorHandlerInstaller().install_global_handler(root)
        MainWindow(root, services).build_ui()

        root.protocol("WM_DELETE_WINDOW", lambda: self._on_close(root))

        return root

    @staticmethod
    def _on_close(root: ttk.Window) -> None:
        logger.info("UI requested shutdown")
        root.quit()
        # root.destroy()
