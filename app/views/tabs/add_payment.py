import ttkbootstrap as ttk
from ttkbootstrap.constants import DANGER, SUCCESS
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.models.exceptions import BusinessRuleError, NotFound
from app.models.models import Movement, RefreshType, Student
from app.services.application_service import ApplicationService
from app.utils.constantes import (
    FONT_BODY,
    MONTH_TO_NUM,
    NUM_TO_MONTH,
    PAD_X,
    PAD_Y,
    TYPE_TRANSLATE,
)
from app.utils.helpers import currency_format
from app.views.helpers_gui import create_label_frame
from app.views.toast import show_toast

TABLE_COLUMNS_PAYMENT = [
    {"text": "id"},
    {"text": "Mes pagado", "stretch": True},
    {"text": "Año pagado", "stretch": True},
    {"text": "Tipo", "stretch": True},
    {"text": "Monto", "stretch": True},
    {"text": "Fecha registrada", "stretch": True},
]

INFO_LABELS = {
    "id_label": "ID:",
    "monthly_fee_label": "Cuota Mensual:",
    "balance_label": "Balance Actual:",
    "ultimo_mes_pagado_label": "Última Fecha Pagada:",
}


class PaymentTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service = main_service

        # UI Elements
        self.id_label: ttk.Label
        self.monthly_fee_label: ttk.Label
        self.balance_label: ttk.Label
        self.ultimo_mes_pagado_label: ttk.Label
        self.student_combobox: ttk.Combobox
        self.month_combobox: ttk.Combobox
        self.amount_entry: ttk.Entry
        self.register_button: ttk.Button
        self.table: Tableview
        self.current_student: Student | None = None
        self._processing: bool = False

        self.frame = ttk.Frame(parent)

        # Initialize data structures
        self._initialize_student_data()
        self._create_widgets()
        self._create_payment_history_table()
        self._create_payment_frame()

        self.main_service.subscribe(RefreshType.STUDENTS, self.refresh_students)
        self.main_service.subscribe(RefreshType.MOVEMENTS, self.refresh_students)

    # Static helpers

    @staticmethod
    def _get_display_name(student: Student) -> str:
        """Creates a consistent display name for the combobox."""
        return f"[{student.id}] {student.last_name}, {student.first_name}"

    @staticmethod
    def _movement_to_row(movement: Movement) -> tuple:
        """Convert payment object to table row."""
        return (
            movement.id,
            NUM_TO_MONTH.get(movement.month, "Desconocido"),
            movement.year,
            TYPE_TRANSLATE[movement.type],
            currency_format(movement.amount),
            movement.created_at.strftime("%d/%m/%Y %H:%M"),
        )

    @staticmethod
    def format_last_payment(movement) -> str:

        if not movement:
            return "Ningún pago registrado"

        return f"{NUM_TO_MONTH[movement.month]} de {movement.year}"

    # Create GUI elements

    def _initialize_student_data(self):
        """Initialize student mapping data."""
        self.all_students = self.main_service.get_students_debtors()
        self.student_map = {s.id: self._get_display_name(s) for s in self.all_students}

    def _create_widgets(self):
        """Create student selection and info widgets."""
        # --- Student Selection Frame ---
        select_frame = create_label_frame(self.frame, "Seleccionar Estudiante", False)
        select_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        ttk.Label(select_frame, text="Estudiante:", font=FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.student_combobox = ttk.Combobox(
            master=select_frame,
            values=list(self.student_map.values()),
            state="normal",
            width=40,
            font=FONT_BODY,
        )
        self.student_combobox.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.student_combobox.bind("<KeyRelease>", self.on_type)
        self.student_combobox.bind("<<ComboboxSelected>>", self._on_student_selected)

        select_frame.columnconfigure(1, weight=1)

        # --- Student Info Frame ---
        self.info_frame = create_label_frame(
            self.frame, "Información del Estudiante", False
        )
        self.info_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        for i, (attr_name, label_text) in enumerate(INFO_LABELS.items()):
            ttk.Label(self.info_frame, text=label_text, font=FONT_BODY).grid(
                row=0, column=i * 2, sticky="w", padx=(0, 5)
            )
            label_widget = ttk.Label(self.info_frame, text="-", font=FONT_BODY)
            label_widget.grid(row=0, column=i * 2 + 1, sticky="w", padx=(0, 15))
            setattr(self, attr_name, label_widget)

    def _create_payment_history_table(self):
        """Create payment history table."""
        history_frame = create_label_frame(self.frame, "Historial de Movimientos", True)
        history_frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)

        self.table = Tableview(
            history_frame,
            coldata=TABLE_COLUMNS_PAYMENT,
            yscrollbar=True,
            autoalign=True,
        )
        self.table.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)

    def _create_payment_frame(self):
        """Create payment registration frame."""
        add_frame = create_label_frame(self.frame, "Registrar Nuevo Pago", False)
        add_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        # Month selection
        ttk.Label(add_frame, text="Mes:", font=FONT_BODY).grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )

        self.month_combobox = ttk.Combobox(
            add_frame, values=[], state="disabled", width=15, font=FONT_BODY
        )
        self.month_combobox.grid(row=0, column=1, sticky="w", padx=(0, 10))

        # Amount entry
        ttk.Label(add_frame, text="Monto pagado ($):", font=FONT_BODY).grid(
            row=0, column=2, sticky="w", padx=(0, 5)
        )
        self.amount_entry = ttk.Entry(add_frame, width=15, state="disabled")
        self.amount_entry.grid(row=0, column=3, sticky="w", padx=(0, 10))
        vcmd = (self.frame.register(lambda P: P.isdigit() or P == ""), "%P")
        self.amount_entry.config(validate="key", validatecommand=vcmd)

        # Register button
        self.register_button = ttk.Button(
            add_frame,
            text="Registrar Pago",
            command=self._register_payment,
            state="disabled",
        )
        self.register_button.grid(row=0, column=4, padx=10)

        add_frame.columnconfigure(1, weight=1)

    # Action funcs

    def on_type(self, event):
        """Filter combobox values based on current input."""
        typed = self.student_combobox.get().lower()
        if typed == "":
            # Reset to full list if input is empty
            self.student_combobox["values"] = list(self.student_map.values())
        else:
            # Filter values that start with the typed text
            filtered = [
                item
                for item in list(self.student_map.values())
                if typed in item.lower()
            ]
            self.student_combobox["values"] = filtered

    def _on_student_selected(self, _event=None):
        """Handle student selection from combobox."""
        text = self.student_combobox.get()

        student_id = int(text.split("]")[0][1:])
        self.current_student = self.main_service.get_student_by_id(student_id)

        self.refresh_students()

    def _update_info_display(
        self, student: Student, balance: int, last_payment: Movement | None
    ):
        """Update student information display."""
        # Update basic info
        self.id_label.config(text=str(student.id))
        self.monthly_fee_label.config(text=currency_format(student.monthly_fee))

        # Update last paid month

        ultimo_text = self.format_last_payment(last_payment)
        self.ultimo_mes_pagado_label.config(text=ultimo_text)

        # Update balance with color coding
        balance_text = currency_format(balance)
        balance_style = SUCCESS if balance >= 0 else DANGER
        self.balance_label.config(text=balance_text, bootstyle=balance_style)

        # Format is (month, year, debt)
        debt_month_list: list[tuple[int, int, int]] = (
            self.main_service.get_unpaid_months_by_student_id(self.current_student.id)
        )

        if not debt_month_list:
            self._enable_payment_controls(False)
            show_toast(self.frame, "No hay cuotas pendientes para pagar", "success")
            return

        month_list = [
            NUM_TO_MONTH[month[0]] + f" {month[1]}" for month in debt_month_list
        ]
        self.month_combobox["values"] = month_list

        # Enable payment controls
        self._enable_payment_controls()
        self._set_default_payment_values(month_list)
        self.amount_entry.focus()

    def _enable_payment_controls(self, value: bool = True):
        """Enable payment-related controls with appropriate defaults."""
        self.month_combobox.config(state="readonly" if value else "disabled")
        self.amount_entry.config(state="normal" if value else "disabled")
        self.register_button.config(state="normal" if value else "disabled")

    def _set_default_payment_values(self, month_list: list[str]) -> None:
        # Set default month to next payable month
        if not month_list:
            self.month_combobox.set("")
            self.register_button.config(state="disabled")
            return

        self.month_combobox.set(month_list[0])

        # Set default amount to student's monthly_fee
        self.amount_entry.delete(0, "end")
        if self.current_student:
            self.amount_entry.insert(0, str(self.current_student.monthly_fee))

    # Action functions

    def _populate_payment_history(self, movements: list[Movement]):
        """Populate payment history table."""
        self.table.delete_rows()
        if not movements:
            self.table.insert_row(
                index="end", values=["-", "-", "-", "Sin movimientos"]
            )
            return

        for m in movements:
            self.table.insert_row(index="end", values=self._movement_to_row(m))
            # if m.type == "PAYMENT":
            #    self.table.apply_table_stripes(stripecolor=("green", "black"))
            # elif m.type == "FEE":
            #    self.table.apply_table_stripes(stripecolor=("orange", "black"))
            # elif m.type == "REVERSED":
            #    self.table.apply_table_stripes(stripecolor=("yellow", "black"))

    def _register_payment(self):
        """Handle payment registration logic."""
        if not self.current_student or not self.current_student.id:
            return

        if self._processing:
            return

        month_year = self.month_combobox.get()
        date = month_year.split()
        month_name = date[0]
        year = int(date[1])

        amount_text = self.amount_entry.get().strip()
        if not amount_text or amount_text == "0":
            show_toast(self.frame, "Ingrese un monto válido", "error")
            return

        amount = int(amount_text)

        confirm = Messagebox.yesno(
            self.format_message(month_name, year, amount),
            "Confirmar pago",
        )

        if confirm != "Yes":
            return

        student_overview = None

        # Process payment
        try:
            self._processing = True
            self._set_processing_state(True)
            month_num = MONTH_TO_NUM[month_name]

            student_overview = self.main_service.add_payment_to_student(
                student_id=self.current_student.id,
                month=month_num,
                year=year,
                amount=amount,
            )

            # Success
            show_toast(self.frame, "Pago registrado con éxito.", "success")

            # self.refresh_students()
            self._populate_payment_history(student_overview.movements)
            self._update_info_display(
                student_overview.student,
                student_overview.balance,
                student_overview.last_payment,
            )

            self.amount_entry.focus()

        except (NotFound, BusinessRuleError) as e:
            show_toast(self.frame, str(e), "error")

        except Exception as e:
            self.main_service.logger.exception("Unexpected payment error")
            Messagebox.show_error(f"Error inesperado: {e}", "Error")

        finally:
            self._processing = False
            self._set_processing_state(False)
            if student_overview and student_overview.balance >= 0:
                self.month_combobox.set("")
                self.amount_entry.delete(0, "end")
                self._enable_payment_controls(False)
                self.student_combobox.set("")
                self.student_combobox.focus()

    def _set_processing_state(self, processing: bool = True):
        """Enable/disable UI while processing payment."""
        self.student_combobox.config("disabled" if processing else "normal")
        self.register_button.config(
            text="Procesando..." if processing else "Registrar Pago",
        )
        self._enable_payment_controls(not processing)

        self.frame.config(cursor="watch" if processing else "")
        self.frame.update_idletasks()

    def format_message(self, month_name, year, amount):
        return f"""👤 {self.current_student.first_name} {self.current_student.last_name}
📅 {month_name} De {year}
💰 {currency_format(amount)}
¿Confirmar pago?"""

    def refresh_students(self):
        """Refresh student list from main service."""
        self._initialize_student_data()
        self.student_combobox["values"] = list(self.student_map.values())

        if self.current_student and self.current_student.id:
            student_overview = self.main_service.get_student_payment_overview(
                self.current_student.id
            )
            self._populate_payment_history(student_overview.movements)
            self._update_info_display(
                student_overview.student,
                student_overview.balance,
                student_overview.last_payment,
            )
