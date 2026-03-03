import threading
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from app.application import Application
from app.bootstrap.app_initializer import AppInitializer
from app.bootstrap.error_handler import GlobalErrorHandler
from app.bootstrap.tk_factory import TkAppFactory
from app.controllers.main_controller import AppController
from app.database.config import DatabaseConfig
from app.main_window import MainWindow
from app.utils.constantes import DATABASE_BACKUP_DIR, DATABASE_PATH
from app.utils.logger import setup_logging


class AppConfig:
    WINDOW_TITLE = "Cuota Pro"
    THEME = "yeti"


class StudentManagerApp:
    def __init__(self, config):
        self.config = config

        self.root: ttk.Window = TkAppFactory.create_root(
            theme=self.config.THEME,
            title=self.config.WINDOW_TITLE,
        )

        GlobalErrorHandler(self.root).install()

        self.db_config = DatabaseConfig(
            db_path=Path(DATABASE_PATH),
            backup_dir=Path(DATABASE_BACKUP_DIR),
        )

        self.initializer = AppInitializer(self.db_config)

        self.controller: AppController | None = None
        self.main_window: MainWindow | None = None

    def initialize(self) -> bool:
        try:
            self.controller = self.initializer.initialize()

            self.controller.create_backup()
            # Background backup
            # threading.Thread(target=self.controller.create_backup, daemon=True).start()

            self.main_window = MainWindow(self.root, self.controller, self.db_config)
            return True

        except Exception as e:
            Messagebox.show_error(
                f"No se pudieron cargar los datos de inicio.\n\nDetalle: {e}",
                "Error Crítico",
            )
            return False

    def run(self):
        if not self.initialize():
            self.root.destroy()
            return

        try:
            self.root.mainloop()
        except Exception as e:
            print("Unexpected error:", e)
        finally:
            try:
                if self.controller:
                    self.controller.create_backup()
            except Exception:
                pass
            finally:
                self.initializer.shutdown()


def main() -> None:
    """Entry point for the application."""
    setup_logging()
    config = AppConfig()
    app = StudentManagerApp(config)
    app.run()


# def main():
#    setup_logging()
#    config = AppConfig()
#    app = Application(config)
#    app.run()


if __name__ == "__main__":
    main()
