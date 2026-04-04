import logging
from typing import Callable

import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.models.models import Movement, RefreshType, Student, StudentOverview
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

COLUMNS = [
    {"text": "ID", "stretch": False},
    {"text": "Apellido"},
    {"text": "Nombre"},
    {"text": "Profesor"},
    {"text": "Balance"},
    {"text": "Ultimo Mes Pagado"},
    {"text": "Estado"},
]


class SearchStudentTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service = main_service
        self.frame = ttk.Frame(parent)
        self.logger = logging.getLogger()

        self._students_cache: dict[int, StudentOverview] = (
            self.main_service.get_students_overview()
        )

        self.main_service.event.subscribe(RefreshType.MOVEMENTS, self._refresh_balances)

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
        self.name_filter_entry.bind(
            "<KeyRelease>", lambda e: self._debounced_search(self.search_by_name)
        )

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

        self.table = Tableview(results_frame, coldata=COLUMNS, yscrollbar=True)

        self.table.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
        self.table.view.bind("<Double-1>", self.on_double_click)

    # Static Methods

    @staticmethod
    def _show_student_details(
        student: Student, last_payment: Movement | None, balance: int
    ):
        phones = [t for t in (student.phone1, student.phone2, student.phone3) if t]
        detalles = f"""
Estado: {"✅ Activo" if student.active else "🚫 Inactivo"}
Nombre: {student.last_name} {student.first_name}
Teléfonos: {", ".join(phones)}
Escuela: {student.school}
Año: {student.year}
Profesor: {student.teacher}
Libro: {student.book}
Curso: {student.course}
Cuota: {student.monthly_fee}
Balance: {currency_format(balance)}
Último mes pagado: {NUM_TO_MONTH.get(last_payment.month, "Desconocido") if last_payment else "Ningun pago registrado"}"""
        Messagebox.show_info(
            detalles, f"Ficha de {student.first_name} {student.last_name}"
        )

    @staticmethod
    def _student_to_row(
        student: Student, balance: int, last_payment: Movement | None
    ) -> tuple:
        return (
            student.id,
            student.last_name,
            student.first_name,
            student.teacher,
            currency_format(balance),
            NUM_TO_MONTH[last_payment.month] if last_payment else "N/A",
            "✅ Activo" if student.active else "🚫 Inactivo",
        )

    # --- Search Actions --- #
    def search_by_name(self):
        self._reset_filters(clear_teacher=True)
        self._run_search(
            lambda: self.main_service.search_student_by_name(
                get_str(self.name_filter_entry)
            )
        )

    def search_by_teacher(self, _event=None):
        self._reset_filters(clear_name=True)
        self._run_search(
            lambda: self.main_service.search_student_by_teacher(
                self.teacher_filter_entry.get()
            )
        )

    def _run_search(self, fetch_fn: Callable[[], dict[int, StudentOverview]]):
        try:
            results = fetch_fn()
            self._populate_table(results)

        except Exception as e:
            self.logger.exception("Error searching students")
            show_toast(self.frame, str(e), "error")

    def show_debtors(self):
        self._reset_filters(clear_teacher=True, clear_name=True)

        self._run_search(self.main_service.get_students_debtors)

    def _debounced_search(self, callback, delay=300):
        if hasattr(self, "_after_id"):
            self.frame.after_cancel(self._after_id)

        self._after_id = self.frame.after(delay, callback)

    def _reset_filters(self, clear_name=False, clear_teacher=False):
        if clear_name:
            self.name_filter_entry.delete(0, "end")
        if clear_teacher:
            self.teacher_filter_entry.set("")

    # --- Table Helpers ---
    def _populate_table(self, overviews: dict[int, StudentOverview]):
        """Limpia la tabla y la llena con la lista proporcionada."""
        self.table.delete_rows()

        for overview in overviews.values():
            row = self.table.insert_row(
                index="end",
                values=self._student_to_row(
                    overview.student, overview.balance, overview.last_payment
                ),
            )

            if overview.balance < 0:
                self.table.view.item(row.iid, tags=("debtor",))

        # self.table.view.tag_configure("debtor", foreground="red")
        # self.table.view.tag_configure("debtor", background="#ffe6e6")

    def _refresh_balances(self):
        self._balances_cache = self.main_service.get_balances_for_students()

    def on_double_click(self, _event):
        rows = self.table.get_rows(selected=True)
        if not rows:
            return

        student_id = rows[0].values[0]

        self._show_student_details(
            self._students_cache[student_id].student,
            self._students_cache[student_id].last_payment,
            self._students_cache[student_id].balance,
        )
