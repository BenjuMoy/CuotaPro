import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.models.exceptions import BusinessRuleError, NotFound
from app.models.models import Movement
from app.services.application_service import ApplicationService
from app.utils.constantes import (
    CAMPO_ID,
    FECHA_HOY_AHORA_FMT,
    FONT_BODY,
    NUM_TO_MONTH,
    PAD_X,
    PAD_Y,
    TYPE_TRANSLATE,
)
from app.utils.helpers import currency_format
from app.views.toast import show_toast

FILTER_ALL = "Todo"
FILTER_PAYMENTS = "Pagos"
FILTER_FEES = "Cuotas"

ADMIN_MOVEMENTS_COLUMNS = (
    CAMPO_ID,
    "ID del estudiante",
    "Tipo",
    "Monto",
    "Mes",
    "Año",
    "Fecha pagada",
)


class MovementTablePanel:
    def __init__(self, frame: ttk.Frame, service: ApplicationService):
        self.frame = frame

        self.main_service = service
        self._processing = False

        self._create_table()

    def _create_table(self):
        """Crea la lista Tableview para mostrar los pagos."""
        self.filter_frame = ttk.Labelframe(self.frame, text="Filtros")
        self.filter_frame.pack(fill="both", padx=PAD_X, pady=PAD_Y, expand=True)
        self.filter_frame.configure(style="Bold.TLabelframe")

        ttk.Label(
            self.filter_frame, text="Filtrar movimientos por: ", font=FONT_BODY
        ).pack(padx=PAD_X, pady=PAD_Y, expand=False)

        self.table_filters = ttk.Combobox(
            self.filter_frame,
            values=[FILTER_ALL, FILTER_PAYMENTS, FILTER_FEES],
            state="readonly",
            font=FONT_BODY,
        )
        self.table_filters.pack(fill="both", padx=PAD_X, pady=PAD_Y, expand=False)
        self.table_filters.set("Todo")

        rows = []

        self.table = Tableview(
            self.filter_frame,
            searchable=True,
            coldata=ADMIN_MOVEMENTS_COLUMNS,
            rowdata=rows,
            yscrollbar=True,
        )

        self.table.pack(expand=True, padx=PAD_X, pady=PAD_Y, fill="both")

        self.table_filters.bind("<<ComboboxSelected>>", self._on_filter_selected)
        self.table.view.bind("<Double-1>", self.handle_double_click)

        self._populate_table(self.table_filters.get())

    # Static Methods

    @staticmethod
    def _movement_to_row(mov: Movement) -> tuple:
        return (
            mov.id,
            mov.student_id,
            TYPE_TRANSLATE[mov.type],
            currency_format(mov.amount),
            NUM_TO_MONTH[mov.month],
            mov.year,
            mov.created_at.strftime(FECHA_HOY_AHORA_FMT),
        )

    # Actions

    def handle_double_click(self, _event):
        if self._processing:
            return

        selected_rows = self.table.get_rows(selected=True)
        if not selected_rows:
            return

        row_values = selected_rows[0].values
        res = Messagebox.yesno(
            f"ID del alumno: {row_values[1]} \nTipo: {row_values[2]} \nFecha: {row_values[6]} \nMonto: {row_values[3]}",
            "Revertir movimiento",
        )

        if res != "Yes":
            show_toast(self.frame, "No se revirtio el movimiento", "warn")
            return

        try:
            self._processing = True
            pago_id = selected_rows[0].values[0]
            self.main_service.reverse_movement(pago_id)

            show_toast(self.frame, "Movimiento revertido", "success")
            self.refresh_table()

        except (NotFound, BusinessRuleError) as e:
            show_toast(self.frame, str(e), "error")

        except Exception:
            Messagebox.show_error("Error al eliminar uno o más movimientos", "error")

        finally:
            self._processing = False

    def _populate_table(self, filter: str = "Todo"):
        self.table.delete_rows()

        if filter == FILTER_PAYMENTS:
            movements = self.main_service.get_effective_payments()
        elif filter == FILTER_FEES:
            movements = self.main_service.get_effective_fees()
        else:
            movements = self.main_service.get_all_movements()

        for mov in movements:
            self.table.insert_row("end", self._movement_to_row(mov))

    def refresh_table(self):
        current_filter = self.table_filters.get()
        self._populate_table(current_filter)

    def _on_filter_selected(self, _event=None):
        self._populate_table(self.table_filters.get())
