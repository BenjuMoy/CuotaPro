import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from application.dto import StudentOverview
from bootstrap.containers import ServiceContainer
from ui.formatters import currency_format
from ui.views.constants import NUM_TO_MONTH, PAD_X, PAD_Y, TEACHERS
from ui.views.helpers_gui import (
    create_label_combobox,
    create_label_entry,
    create_label_frame,
    get_str,
)
from ui.views.toast import show_toast

# TODO make filters horizontal or vertical on the side of the tableview
# TODO update and add payment from here

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
    def __init__(self, parent: ttk.Notebook, main_service: ServiceContainer):
        self.s = main_service
        self.frame = ttk.Frame(parent)

        self._create_widgets()
        self._create_results_table()

    def _create_widgets(self):
        search_frame = create_label_frame(self.frame, "Filtros", False)
        search_frame.columnconfigure(1, weight=1)

        # --- Row 0: Name --- #
        self.name_filter_entry = create_label_entry(
            search_frame, "Apellido / nombre", 0, 0
        )
        self.name_filter_entry.bind(
            "<KeyRelease>", lambda e: self._debounced_search(self.search_students)
        )

        # --- Row 1: Teacher --- #
        self.teacher_filter_entry = create_label_combobox(
            search_frame, "Profesor", 1, 0, ["Todos"] + TEACHERS
        )
        self.teacher_filter_entry.set("Todos")
        self.teacher_filter_entry.bind(
            "<<ComboboxSelected>>", lambda e: self.search_students()
        )

        # --- Row 2: Active filter --- #
        self.active_filter = create_label_combobox(
            search_frame, "Estado", 2, 0, ["Todos", "Activos", "Inactivos"]
        )
        self.active_filter.set("Todos")
        self.active_filter.bind(
            "<<ComboboxSelected>>", lambda e: self.search_students()
        )

        # --- Row 3: Debtors toggle --- #
        self.debtors_var = ttk.BooleanVar(value=False)
        debtors_check = ttk.Checkbutton(
            search_frame,
            text="Solo deudores",
            variable=self.debtors_var,
            command=self.search_students,
        )
        debtors_check.grid(
            row=3, column=0, columnspan=2, sticky="w", padx=PAD_X, pady=PAD_Y
        )

    def _create_results_table(self):
        """create Tableview for results."""
        results_frame = create_label_frame(self.frame, "Resultados", True)

        self.table = Tableview(results_frame, coldata=COLUMNS, yscrollbar=True)

        self.table.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
        self.table.view.bind("<Double-1>", self.on_double_click)

    # Static Methods

    @staticmethod
    def _show_student_details(o: StudentOverview):
        phones = [
            t
            for t in (
                o.student.phone1,
                o.student.phone2,
                o.student.phone3,
            )
            if t
        ]

        detalles = f"""--- Datos personales ---
Estado: {"✅ Activo" if o.student.active else "🚫 Inactivo"}
Nombre: {o.student.last_name} {o.student.first_name}
Teléfonos: {", ".join(phones)}

--- Académico ---
Escuela: {o.student.school}
Año: {o.student.school_year}
Profesor: {o.student.teacher}
Libro: {o.student.book}
Curso: {o.student.course}
Cuota: {o.student.monthly_fee}

--- Financiero ---
Balance: {currency_format(o.balance)}
Último mes pagado: {NUM_TO_MONTH.get(o.last_payment.month, "Sin Pagos") if o.last_payment else "Sin Pagos"}"""
        Messagebox.show_info(
            detalles,
            f"Ficha de {o.student.first_name} {o.student.last_name}",
        )

    @staticmethod
    def _student_to_row(o: StudentOverview) -> tuple:
        last_payment = o.movements[0] if o.movements else None

        return (
            o.student.id,
            o.student.last_name,
            o.student.first_name,
            o.student.teacher,
            currency_format(o.balance),
            NUM_TO_MONTH[last_payment.month] if last_payment else "Sin Pagos",
            "✅ Activo" if o.student.active else "🚫 Inactivo",
        )

    # --- Search Actions --- #
    def search_students(self):
        try:
            name = get_str(self.name_filter_entry)

            teacher = self.teacher_filter_entry.get()
            teacher = None if teacher == "Todos" else teacher

            active_value = self.active_filter.get()
            if active_value == "Activos":
                active = True
            elif active_value == "Inactivos":
                active = False
            else:
                active = None

            only_debtors = self.debtors_var.get()

            results = self.s.cqrs.search_students(
                name=name,
                teacher=teacher,
                active=active,
                only_debtors=only_debtors,
            )

            self._populate_table(results)

        except Exception as e:
            show_toast(self.frame, str(e), "error")

    def _debounced_search(self, callback, delay=300):
        if hasattr(self, "_after_id"):
            self.frame.after_cancel(self._after_id)

        self._after_id = self.frame.after(delay, callback)

    # --- Table Helpers ---
    def _populate_table(self, overviews: dict[int, StudentOverview]):
        """Limpia la tabla y la llena con la lista proporcionada."""
        self.table.delete_rows()

        for overview in overviews.values():
            row = self.table.insert_row(
                index="end",
                values=self._student_to_row(overview),
            )

            if overview.balance < 0:
                self.table.view.item(row.iid, tags=("debtor",))

        # self.table.view.tag_configure("debtor", foreground="red")
        # self.table.view.tag_configure("debtor", background="#ffe6e6")

    def on_double_click(self, _event):
        rows = self.table.get_rows(selected=True)
        if not rows:
            return

        student_id = rows[0].values[0]

        self._show_student_details(self.s.cqrs.get_overview_by_id(student_id))
