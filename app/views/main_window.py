import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from app.services.application_service import ApplicationService
from app.views.dialogs.about_dialog import show_about
from app.views.dialogs.database_stats_dialog import ShowDatabasrStatsDialog
from app.views.dialogs.restore_backup_dialog import RestoreBackupDialog
from app.views.tabs.add_payment import PaymentTab
from app.views.tabs.add_student import AddStudentTab
from app.views.tabs.administrative import AdministrativeTab
from app.views.tabs.analytics import AnalyticsTab
from app.views.tabs.dashboard import DashboardTab
from app.views.tabs.informes_gui import ReportsTab
from app.views.tabs.search_students import SearchStudentTab
from app.views.tabs.update_student import UpdateStudentTab

MENU_LAYOUT = [
    {
        "label": "Archivo",
        "items": [
            {"label": "Crear Respaldo", "command": "create_backup"},
            {"separator": True},
            {"label": "Restaurar Respaldo", "command": "restore_backup"},
        ],
    },
    {
        "label": "Base de Datos",
        "items": [
            {"label": "Verificar Integridad", "command": "verify_integrity"},
        ],
    },
    {
        "label": "Sobre",
        "items": [{"label": "Sobre la aplicacion", "command": "show_about"}],
    },
]

TAB_LAYOUT = [
    {
        "name": "dashboard_tab",
        "cls": DashboardTab,
        "label": "Inicio",
    },
    {
        "name": "add_student_tab",
        "cls": AddStudentTab,
        "label": "Agregar Estudiante",
    },
    {
        "name": "search_student_tab",
        "cls": SearchStudentTab,
        "label": "Buscar Estudiantes",
    },
    {
        "name": "update_student_tab",
        "cls": UpdateStudentTab,
        "label": "Modificar Estudiantes",
    },
    {
        "name": "payments_tab",
        "cls": PaymentTab,
        "label": "Agregar Pago",
    },
    {
        "name": "reports_tab",
        "cls": ReportsTab,
        "label": "Reportes",
    },
    {
        "name": "administrative_tab",
        "cls": AdministrativeTab,
        "label": "Administrativo",
    },
    {
        "name": "analytics_tab",
        "cls": AnalyticsTab,
        "label": "Analitics",
    },
]


class MainWindow:
    """Main window of the application."""

    def __init__(
        self,
        root: ttk.Window,
        main_service: ApplicationService,
    ):
        """Initialize the main window.
        Args:
            root: The root window
            main_service: The application main_service
            db_config: The application config
        """
        self.root = root
        self.main_service = main_service

        self.notebook: ttk.Notebook
        self.status_bar: ttk.Label

        # Create UI components
        self._create_ui()

        self.main_service.subscribe(self.refresh_students)

    def _create_ui(self):
        """Create the user interface components."""
        self._build_menu(MENU_LAYOUT)
        self._setup_notebook(TAB_LAYOUT)
        self._setup_status_bar()

    def _build_menu(self, layout):
        COMMANDS = {
            "create_backup": self.create_backup,
            "restore_backup": self.restore_backup,
            "verify_integrity": self.verify_integrity,
            "show_about": self.show_about,
        }

        menubar = ttk.Menu(self.root)
        self.root.config(menu=menubar)

        for menu_conf in layout:
            menu = ttk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label=menu_conf["label"], menu=menu)

            for item in menu_conf["items"]:
                if item.get("separator"):
                    menu.add_separator()
                else:
                    (
                        menu.add_command(
                            label=item["label"],
                            command=COMMANDS[item["command"]],
                        )
                    )

    def _setup_notebook(self, layout):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        for tab_config in layout:
            tab_instance = tab_config["cls"](self.notebook, self.main_service)

            setattr(self, tab_config["name"], tab_instance)

            self.notebook.add(tab_instance.frame, text=tab_config["label"])

    def _setup_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Label(
            self.root, text="Listo", relief="sunken", anchor="w"
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.refresh_students()

    def update_status(self, message: str, duration: int = 5000):
        """Update the status bar with a message. Args: message: The message to display"""
        self.status_bar.config(text=message)
        self.root.after(duration, lambda: self.update_status("Listo"))

    def refresh_students(self):
        count = self.main_service.get_active_student_count()
        self.update_status(f"{count} estudiantes activos")

    def create_backup(self):
        """Create a backup of the database."""
        try:
            backup_path = self.main_service.create_backup()
            Messagebox.show_info(
                f"Respaldo creado en:\n{backup_path}", "Respaldo Creado"
            )
            self.update_status("Respaldo creado")
        except Exception as e:
            Messagebox.show_error(f"Error al crear respaldo: {e}", "Error")

    def restore_backup(self):
        """Restore a backup of the database."""
        try:
            RestoreBackupDialog(self.root, self.main_service)
        except Exception as e:
            Messagebox.show_error(f"Error al restaurar respaldo: {e}", "Error")

    def verify_integrity(self):
        """Verify the integrity of the database."""
        try:
            status = self.main_service.verify_integrity()
            if status:
                Messagebox.show_info(
                    "La base de datos está íntegra", "Verificación Completada"
                )
                self.update_status("Verificación de integridad completada")
            else:
                Messagebox.show_warning(
                    "La base de datos tiene problemas de integridad", "Advertencia"
                )
                self.update_status("Problemas de integridad detectados")
        except Exception as e:
            Messagebox.show_error(f"Error al verificar integridad: {e}", "Error")

    def show_database_stats(self):
        """Show database statistics."""
        try:
            ShowDatabasrStatsDialog(self.root, self.main_service)

            self.update_status("Estadísticas de base de datos mostradas")
        except Exception as e:
            Messagebox.show_error(f"Error al obtener estadísticas: {e}", "Error")

    def export_to_csv(self):
        """Export database to CSV files."""
        try:
            export_path = self.main_service.export_to_csv()
            Messagebox.show_info(
                f"Datos exportados a:\n{export_path}", "Exportación Completada"
            )
            self.update_status("Datos exportados a CSV")
        except Exception as e:
            Messagebox.show_error(f"Error al exportar datos: {e}", "Error")

    def show_about(self):
        show_about(self.root)
