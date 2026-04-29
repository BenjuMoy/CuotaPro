import logging
import sys
import traceback

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

logger = logging.getLogger(__name__)


class ErrorHandlerInstaller:
    def install_global_handler(self, root: ttk.Window):
        def handle_exception(exc_type, exc_value, exc_traceback):
            error_msg = f"{exc_type.__name__}: {exc_value}"
            logger.error(
                "Unhandled exception",
                exc_info=(exc_type, exc_value, exc_traceback),
            )

            try:
                root.after(
                    0,
                    lambda: Messagebox.show_error(
                        f"Se produjo un error inesperado:\n\n{error_msg}",
                        "Error Crítico",
                    ),
                )

            except Exception:
                logger.exception("Failed to show error dialog")

        sys.excepthook = handle_exception
        root.report_callback_exception = handle_exception
