import logging
from typing import Callable

import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.models.models import Movement, Student
from app.services.application_service import ApplicationService
from app.utils.constantes import ICON_SEARCH, NUM_TO_MONTH, PAD_X, PAD_Y, TEACHERS
from app.utils.helpers import currency_format
from app.views.helpers_gui import (
    create_label_combobox,
    create_label_entry,
    create_label_frame,
    get_str,
)
from app.views.toast import show_toast


class SearchStudentTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service = main_service
        self.frame = ttk.Frame(parent)
        self.logger = logging.getLogger(__name__)

        self._create_widgets()
        self._create_results_table()

    def _create_widgets(self):
        """Create search fields and buttons for form."""
        search_frame = create_label_frame(self.frame, "Filtros", False)
        search_frame.columnconfigure(1, weight=1)

        # --- Row 0: Student Name Search --- #
        self.name_filter_entry = create_label_entry(
            search_frame, "Apellido / nombre", 0, 0
        )
        self.image = ttk.PhotoImage(file=ICON_SEARCH)
        student_name = ttk.Button(
            search_frame,
            text="Buscar",
            image=self.image,
            compound="right",
            command=self.search_by_name,
        )
        student_name.grid(row=0, column=2, padx=PAD_X, pady=PAD_Y)
        self.name_filter_entry.bind("<KeyRelease>", lambda e: self.search_by_name())

        # --- Row 1: Teacher Filter --- #
        self.teacher_filter_entry = create_label_combobox(
            search_frame, "Profesor", 1, 0, TEACHERS
        )
        self.teacher_filter_entry.bind("<<ComboboxSelected>>", self.search_by_teacher)

        # --- Separator --- #
        ttk.Separator(search_frame, orient="horizontal").grid(
            row=2, column=1, padx=PAD_X, pady=PAD_Y, sticky="ew"
        )

        # --- Row 2: Show Debtors --- #
        btn_debtors = ttk.Button(
            search_frame, text="Ver Deudores", command=self.show_debtors
        )
        btn_debtors.grid(row=3, column=0, columnspan=3, pady=PAD_Y, sticky="ew")

    def _create_results_table(self):
        """create Tableview for results."""
        results_frame = create_label_frame(self.frame, "Resultados", True)

        # Define columns
        coldata = [
            {"text": "ID", "stretch": False},
            {"text": "Apellido"},
            {"text": "Nombre"},
            {"text": "Profesor"},
            {"text": "Balance"},
            {"text": "Estado"},
        ]

        self.table = Tableview(results_frame, coldata=coldata, yscrollbar=True)

        self.table.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
        self.table.view.bind("<Double-1>", self.on_double_click)

    # Static Methods

    @staticmethod
    def _show_student_details(
        est: Student, last_payment: Movement | None, balance: int
    ):
        phones = [t for t in (est.phone1, est.phone2, est.phone3) if t]
        detalles = f"""
Estado: {"✅ Activo" if est.active else "🚫 Inactivo"}
Nombre: {est.last_name} {est.first_name}
Teléfonos: {", ".join(phones)}
Escuela: {est.school}
Año: {est.year}
Profesor: {est.teacher}
Libro: {est.book}
Curso: {est.course}
Cuota: {est.monthly_fee}
Balance: {currency_format(balance)}
Último mes pagado: {NUM_TO_MONTH.get(last_payment.month, "Desconocido") if last_payment else "Ningun pago registrado"}
    """
        Messagebox.show_info(detalles, f"Ficha de {est.first_name} {est.last_name}")

    @staticmethod
    def _student_to_row(est: Student, balance: int) -> tuple:
        return (
            est.id,
            est.last_name,
            est.first_name,
            est.teacher,
            currency_format(balance),
            "✅ Activo" if est.active else "🚫 Inactivo",
        )

    # --- Search Actions --- #
    def search_by_name(self):
        self.teacher_filter_entry.set("")
        name = get_str(self.name_filter_entry)
        self._run_search(
            lambda: self.main_service.search_student_by_name(name),
            "No se encontraron estudiantes con ese nombre o apellido",
        )

    def search_by_teacher(self, _event=None):
        self.name_filter_entry.delete(0, "end")
        self._run_search(
            lambda: self.main_service.search_student_by_teacher(
                self.teacher_filter_entry.get()
            ),
            "No se encontraron alumnos con ese profesor",
        )

    def _run_search(self, fetch_fn: Callable[[], list[Student]], empty_msg: str):
        try:
            results = fetch_fn()
            self._populate_table(results)

            if not results:
                self.table.insert_row("end", ["", empty_msg, "", "", "", ""])

        except Exception:
            self.logger.exception("Error searching students")
            show_toast(self.frame, "Error buscando estudiantes", "error")

    def show_debtors(self):
        self.name_filter_entry.delete(0, "end")
        self.teacher_filter_entry.set("")

        self._run_search(
            self.main_service.get_students_debtors,
            "No se encontraron estudiantes deudores",
        )

    # --- Table Helpers ---
    def _populate_table(self, students: list[Student]):
        """Limpia la tabla y la llena con la lista proporcionada."""
        self.table.delete_rows()
        students = sorted(
            students, key=lambda s: (s.last_name.lower(), s.first_name.lower())
        )

        for est in students:
            student_overview = self.main_service.get_student_payment_overview(est.id)
            row = self.table.insert_row(
                index="end", values=self._student_to_row(est, student_overview.balance)
            )

            if student_overview.balance < 0:
                self.table.view.item(row.iid, tags=("debtor",))

    def on_double_click(self, _event):
        rows = self.table.get_rows(selected=True)
        if not rows:
            return

        student_id = rows[0].values[0]

        student_overview = self.main_service.get_student_payment_overview(student_id)
        self._show_student_details(
            student_overview.student,
            student_overview.last_payment,
            student_overview.balance,
        )
