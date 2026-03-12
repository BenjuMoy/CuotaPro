import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.services.application_service import ApplicationService
from app.utils.helpers import currency_format
from app.views.toast import show_toast

from ...utils.constantes import FONT_BODY, PAD_X, PAD_Y, TEACHERS
from ..helpers_gui import (
    create_label_combobox,
    create_label_frame,
)


class ReportsTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service: ApplicationService = main_service
        self.frame = ttk.Frame(parent)

        self.main_service.subscribe(self.refresh_student_list)

        self._create_widgets()
        self._create_results_table()

    def _create_widgets(self):
        # --- Search Area ---
        search_frame = create_label_frame(self.frame, "Cálcular Sueldos", False)

        self.cb = create_label_combobox(search_frame, "Profesor", 0, 0, TEACHERS)
        self.cb.bind("<<ComboboxSelected>>", self._on_teacher_selected)

        search_frame.columnconfigure(1, weight=1)

    def _create_results_table(self):
        # --- Results Display Area ---
        # We use a frame to hold the summary labels and the table
        self.results_frame: ttk.Labelframe = ttk.Labelframe(
            self.frame, text="Estudiantes Registrados"
        )
        self.results_frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
        self.results_frame.configure(style="Bold.TLabelframe")

        # 1. Summary Labels (Initially hidden or empty)
        self.summary_text_var: ttk.StringVar = ttk.StringVar()
        self.summary_label: ttk.Label = ttk.Label(
            self.results_frame,
            textvariable=self.summary_text_var,
            font=FONT_BODY,
        )
        self.summary_label.pack(pady=(0, 10))

        # 2. Breakdown Table
        cols = ("Apellido", "Nombre", "Cuota Aportada")
        self.table = Tableview(self.results_frame, coldata=cols)

        self.table.pack(side="left", fill="both", expand=True)

    def calculate_salary(self):
        """Fetches data from main service and updates the UI."""
        prof_name = self.cb.get()
        if not prof_name:
            return

        try:
            # self.search_btn.config(state="disabled", text="Calculando...")
            self.frame.update()  # Force UI update

            # Get clean data from main service
            report = self.main_service.get_salary_report(prof_name)

            # 1. Update Summary Text
            summary = (
                f"Profesor: {report['teacher']}\n"
                f"Total a Pagar: {currency_format(int(report['total']))}\n"
                f"Basado en {report['student_count']} estudiantes activos"
            )
            self.summary_text_var.set(summary)

            # 2. Clear previous table data
            self._clear_table()

            # 3. Populate table with breakdown
            for detail in report["details"]:
                values = (
                    detail["last_name"],
                    detail["first_name"],
                    detail["monthly_fee"],
                )
                self.table.insert_row(index="end", values=values)

        except ValueError as e:
            # Clear UI on error
            self.summary_text_var.set("")
            self._clear_table()
            show_toast(self.frame, str(e), "warn")
        except Exception as e:
            Messagebox.show_error(
                str(e),
                "Error Inesperado",
            )

    def _clear_table(self):
        self.table.delete_rows()

    def refresh_student_list(self):
        """Called by main service if data changes (optional)."""
        # You might want to clear the report if data changes to avoid showing stale numbers
        self.summary_text_var.set("")
        self._clear_table()

    def _on_teacher_selected(self, event):
        display_name = self.cb.get()
        if not display_name:
            return

        if display_name:
            self.calculate_salary()
        else:
            self._clear_table()
