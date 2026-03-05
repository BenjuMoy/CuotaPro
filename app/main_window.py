from tkinter import Listbox

import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from app.services.application_service import ApplicationService
from app.utils.constantes import ABOUT_TEXT, APP_VERSION, FONT_HEADER
from app.views.tabs.add_payment import PaymentTab
from app.views.tabs.add_student import AddStudentTab
from app.views.tabs.administrative import AdministrativeTab
from app.views.tabs.dashboard import DashboardTab
from app.views.tabs.informes_gui import ReportsTab
from app.views.tabs.search_students import SearchStudentTab
from app.views.tabs.update_student import UpdateStudentTab

MENU_LAYOUT = [
    {
        "label": "Archivo",
        "items": [{"label": "Cargar archivo", "command": "load_file"}],
    },
    {
        "label": "Base de Datos",
        "items": [
            {"label": "Crear Respaldo", "command": "create_backup"},
            {"label": "Verificar Integridad", "command": "verify_integrity"},
            {"separator": True},
            {"label": "Restaurar Respaldo", "command": "restore_backup"},
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
        "label": "Resumen",
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
]


class MainWindow:
    """Main window of the application."""

    def __init__(
        self,
        root: ttk.Window,
        controller: ApplicationService,
    ):
        """Initialize the main window.
        Args:
            root: The root window
            controller: The application controller
            db_config: The application config
        """
        self.root = root
        self.main_service = controller

        self.notebook: ttk.Notebook
        self.status_bar: ttk.Label

        # Create UI components
        self._create_ui()

        self.main_service.subscribe(self.refresh_students)

    def _create_ui(self):
        """Create the user interface components."""
        self._setup_style()
        self._build_menu(MENU_LAYOUT)
        self._setup_notebook(TAB_LAYOUT)
        self._setup_status_bar()

    def _setup_style(self):
        """Configure the UI style."""
        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=(FONT_HEADER))

    def _build_menu(self, layout):
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
                        command=getattr(self, item["command"]),
                    )

    def _setup_notebook(self, layout):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        for tab_config in layout:
            tab_instance = tab_config["cls"](self.notebook, self.main_service)

            setattr(self, tab_config["name"], tab_instance)

            self.notebook.add(tab_instance.frame, text=tab_config["label"])

        # self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _setup_status_bar(self):
        """Create the status bar."""
        count = self.main_service.get_active_student_count()

        self.status_bar = ttk.Label(
            self.root, text="Listo", relief="sunken", anchor="w"
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.update_status(f"{count} estudiantes activos")

    def update_status(self, message: str):
        """Update the status bar with a message. Args: message: The message to display"""
        self.status_bar.config(text=message)

    def refresh_students(self):
        count = self.main_service.get_active_student_count()
        self.update_status(f"{count} estudiantes activos")

    def load_file(self): ...

    def show_about(self):
        dialog = ttk.Toplevel(self.root)
        dialog.title("Sobre la Aplicación")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text="Gestor de Estudiantes",
            font=(FONT_HEADER),
        ).pack(pady=10)

        ttk.Label(
            dialog,
            text=f"Versión {APP_VERSION}",
            font=("Helvetica", 12),
        ).pack(pady=5)

        ttk.Label(
            dialog,
            text="Sistema de gestión para academias.\n\n"
            "Permite controlar estudiantes, pagos,\n"
            "deudas y salarios docentes.",
            justify="center",
        ).pack(pady=10)

        ttk.Label(
            dialog,
            text=ABOUT_TEXT,
            font=("Helvetica", 10),
        ).pack(pady=10)

        ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=15)

    def create_backup(self):
        """Create a backup of the database."""
        try:
            backup_path = self.main_service.create_backup()
            Messagebox.show_info(
                f"Respaldo creado en:\n{backup_path}", "Respaldo Creado"
            )
            self.update_status("Respaldo creado")
            self.root.after(3000, lambda: self.update_status("Listo"))
        except Exception as e:
            Messagebox.show_error(f"Error al crear respaldo: {e}", "Error")

    def restore_backup(self):
        """Restore a backup of the database."""
        # Create a dialog to select backup file
        dialog = ttk.Toplevel(self.root)
        dialog.title("Restaurar Respaldo")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Seleccione un archivo de respaldo:").pack(pady=10)

        # List available backup files
        backup_files = self.main_service.list_backup_files()

        listbox = Listbox(dialog)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for backup_file in backup_files:
            listbox.insert("end", f"{backup_file.name} - {backup_file.stat().st_mtime}")

        def restore_selected():
            try:
                confirm = Messagebox.yesno(
                    "Esto reemplazará la base de datos actual.\n\n"
                    "Se recomienda crear un respaldo antes de continuar.\n\n"
                    "¿Desea continuar?",
                    "Confirmar Restauración",
                )
                if confirm != "Yes":
                    return

                selection = listbox.curselection()
                if not selection:
                    Messagebox.show_warning(
                        "Seleccione un archivo de respaldo", "Advertencia"
                    )
                    return

                selected_file = backup_files[selection[0]]
                if self.main_service.restore_backup(str(selected_file)):
                    Messagebox.show_info("Respaldo restaurado correctamente", "Éxito")
                    self.update_status("Respaldo restaurado")
                    # Restart the application to reload the data
                    self.root.destroy()
                    # self.root.event_generate("<<RestartApp>>")
                else:
                    Messagebox.show_error("Error al restaurar respaldo", "Error")
                dialog.destroy()
            except Exception as e:
                Messagebox.show_error(f"Error al restaurar respaldo: {e}", "Error")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Restaurar", command=restore_selected).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(
            side="left", padx=5
        )

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
            stats = self.main_service.get_database_stats()

            # Create a dialog to display stats
            dialog = ttk.Toplevel(self.root)
            dialog.title("Estadísticas de Base de Datos")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()

            stats_text = f"""
            Base de Datos Existe: {stats["exists"]}
            Tamaño: {stats["size_mb"]} MB
            Número de Estudiantes: {stats["student_count"]}
            Número de Pagos: {stats["payment_count"]}
            Última Modificación: {stats["last_modified"]}
            """

            text_widget = ttk.Text(dialog, wrap="word")
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", stats_text)
            text_widget.config(state="disabled")

            ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=10)

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
