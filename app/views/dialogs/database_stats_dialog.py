import ttkbootstrap as ttk

from app.services.application_service import ApplicationService


class ShowDatabasrStatsDialog:
    def __init__(self, parent: ttk.Window, main_service: ApplicationService):
        self.parent = parent
        self.main_service = main_service

        self.get_database_stats

    def get_database_stats(self):
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
