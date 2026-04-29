from typing import Callable

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from application.events import RefreshType
from bootstrap.containers import ServiceContainer
from ui.views.dialogs.about_dialog import show_about
from ui.views.dialogs.database_stats_dialog import ShowDatabaseStatsDialog
from ui.views.dialogs.restore_backup_dialog import RestoreBackupDialog
from ui.views.tabs.add_payment import PaymentTab
from ui.views.tabs.add_student import AddStudentTab
from ui.views.tabs.administrative import AdministrativeTab
from ui.views.tabs.analytics import AnalyticsTab
from ui.views.tabs.dashboard import DashboardTab
from ui.views.tabs.informes_gui import ReportsTab
from ui.views.tabs.search_students import SearchStudentTab
from ui.views.tabs.update_student import UpdateStudentTab

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
        "label": "Sistema",
        "items": [
            {"label": "Verificar Integridad", "command": "verify_integrity"},
        ],
    },
    {
        "label": "Sobre",
        "items": [{"label": "Sobre la aplicacion", "command": "show_about"}],
    },
]

# TODO Pass deps individually per tab

TAB_LAYOUT = [
    (DashboardTab, "Inicio"),
    (AddStudentTab, "Agregar Estudiante"),
    (SearchStudentTab, "Buscar Estudiantes"),
    (UpdateStudentTab, "Modificar Estudiantes"),
    (PaymentTab, "Agregar Pago"),
    (ReportsTab, "Reportes"),
    (AdministrativeTab, "Administrativo"),
    (AnalyticsTab, "Analitics"),
]


class MainWindow:
    def __init__(self, root: ttk.Window, services: ServiceContainer):
        self.root = root
        self.services = services

        # UI pieces
        self.status_bar = StatusBar(root)

        self._commands = {
            "create_backup": self.create_backup,
            "restore_backup": self.restore_backup,
            "verify_integrity": self.verify_integrity,
            "show_about": self.show_about,
        }

    def build_ui(self):
        MenuBar(self.root, self._commands).build(MENU_LAYOUT)

        tab_builder = TabBuilder(self.root, self.services)
        self.notebook, self.tabs = tab_builder.build(TAB_LAYOUT)

        self.services.event.subscribe(RefreshType.STUDENTS, self.refresh_students)

        self.refresh_students()

    def _run_action(self, action, success_msg=None):
        try:
            result = action()

            if success_msg:
                Messagebox.show_info(success_msg.format(result=result))

            return result

        except Exception as e:
            Messagebox.show_error(f"Error: {e}", "Error")

    def create_backup(self):
        """Create a backup of the database."""
        self._run_action(
            self.services.maintenance.create_backup,
            success_msg="Respaldo creado en:\n{result}",
        )
        self.status_bar.set("Respaldo creado")

    def restore_backup(self):
        """Restore a backup of the database."""
        try:
            RestoreBackupDialog(self.root, self.services)
        except Exception as e:
            Messagebox.show_error(f"Error al restaurar respaldo: {e}", "Error")

    def verify_integrity(self):
        """Verify the integrity of the database."""
        try:
            status = self.services.maintenance.verify_integrity()
            if status:
                Messagebox.show_info(
                    "La base de datos está íntegra", "Verificación Completada"
                )
                self.status_bar.set("Verificación de integridad completada")
            else:
                Messagebox.show_warning(
                    "La base de datos tiene problemas de integridad", "Advertencia"
                )
                self.status_bar.set("Problemas de integridad detectados")
        except Exception as e:
            Messagebox.show_error(f"Error al verificar integridad: {e}", "Error")

    def show_database_stats(self):
        """Show database statistics."""
        try:
            ShowDatabaseStatsDialog(self.root, self.services)

            self.status_bar.set("Estadísticas de base de datos mostradas")
        except Exception as e:
            Messagebox.show_error(f"Error al obtener estadísticas: {e}", "Error")

    def export_to_csv(self):
        """Export database to CSV files."""
        try:
            export_path = self.services.maintenance.export_to_csv()
            Messagebox.show_info(
                f"Datos exportados a:\n{export_path}", "Exportación Completada"
            )
            self.status_bar.set("Datos exportados a CSV")
        except Exception as e:
            Messagebox.show_error(f"Error al exportar datos: {e}", "Error")

    def show_about(self):
        show_about(self.root)

    def refresh_students(self):
        count = self.services.cqrs.get_active_count()
        self.status_bar.set(f"Estudiantes activos {count}")


class TabBuilder:
    def __init__(self, root: ttk.Window, services: ServiceContainer):
        self.root = root
        self.services = services
        self.notebook = ttk.Notebook(root)

    def build(self, layout):
        self.notebook.pack(fill="both", expand=True)

        instances = {}

        for tab_cls, label in layout:
            tab = tab_cls(self.notebook, self.services)
            instances[tab_cls.__name__] = tab
            self.notebook.add(tab.frame, text=label)

        return self.notebook, instances


class StatusBar:
    def __init__(self, root: ttk.Window):
        self.root = root
        self.label = ttk.Label(root, text="Listo", relief="sunken", anchor="w")
        self.label.pack(side="bottom", fill="x")

    def set(self, message: str, duration: int = 5000):
        self.label.config(text=message)
        self.root.after(duration, lambda: self.label.config(text="Listo"))


class MenuBar:
    def __init__(self, root, commands: dict[str, Callable]):
        self.root = root
        self.commands = commands

    def build(self, layout):
        menubar = ttk.Menu(self.root)
        self.root.config(menu=menubar)

        for menu_conf in layout:
            menu = ttk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label=menu_conf["label"], menu=menu)

            for item in menu_conf["items"]:
                if item.get("separator"):
                    menu.add_separator()
                else:
                    menu.add_command(
                        label=item["label"],
                        command=self.commands[item["command"]],
                    )
