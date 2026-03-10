import logging
import sys
import traceback

from ttkbootstrap.dialogs import Messagebox

logger = logging.getLogger(__name__)


class GlobalErrorHandler:
    """sets up the global error handler."""

    def __init__(self, root):
        self.root = root

    def install(self):
        def handle_exception(exc_type, exc_value, exc_traceback):
            error_msg = f"{exc_type.__name__}: {exc_value}"

            try:
                self.root.after(
                    0,
                    lambda: Messagebox.show_error(
                        f"Error no controlado:\n\n{error_msg}",
                        "Error Crítico",
                    ),
                )
            except Exception:
                logger.error("Fatal error: %s", error_msg)

            logger.exception("Unhandled exception")

        sys.excepthook = handle_exception
        self.root.report_callback_exception = handle_exception
