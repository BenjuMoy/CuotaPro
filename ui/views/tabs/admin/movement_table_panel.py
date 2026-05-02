import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from application.dto import MovementDTO
from application.events import RefreshType
from bootstrap.containers import ServiceContainer
from domain.shared.exceptions import BusinessRuleError, NotFound
from domain.shared.shared import MovementType
from ui.formatters import currency_format
from ui.views.constants import FONT_BODY, NUM_TO_MONTH, PAD_X, PAD_Y, TYPE_TRANSLATE
from ui.views.toast import show_toast

FILTER_ALL = "Todo"
FILTER_PAYMENTS = "Pagos"
FILTER_FEES = "Cuotas"

ADMIN_MOVEMENTS_COLUMNS = (
    "ID",
    "ID del estudiante",
    "Tipo",
    "Monto",
    "Mes",
    "Año",
    "Fecha pagada",
)


class MovementTablePanel:
    def __init__(self, frame: ttk.Frame, service: ServiceContainer):
        self.frame = frame
        self.s = service
        self._processing = False

        self.s.event.subscribe(RefreshType.MOVEMENTS, self.refresh_table)

        self._movements_cache: list[MovementDTO] = self.s.cqrs.get_all_movements()

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
    def _movement_to_row(mov: MovementDTO) -> tuple:
        return (
            mov.id,
            mov.student_id,
            TYPE_TRANSLATE[mov.type],
            currency_format(mov.amount),
            NUM_TO_MONTH[mov.month],
            mov.year,
            mov.created_at,
        )

    # Actions

    def handle_double_click(self, _event):
        if self._processing:
            return

        selected_rows = self.table.get_rows(selected=True)
        if not selected_rows:
            return

        row_values = selected_rows[0].values
        confirm = Messagebox.yesno(f"""
⚠ Reversión de movimiento

Alumno ID: {row_values[1]}
Monto: {row_values[3]}
Fecha: {row_values[6]}

Esta acción no se puede deshacer.

¿Confirmar?""")

        if confirm != "Yes":
            show_toast(self.frame, "No se revirtio el movimiento", "warn")
            return

        try:
            self._processing = True
            payment_id = selected_rows[0].values[0]
            self.s.accounting.reverse(payment_id)

            show_toast(self.frame, "Movimiento revertido", "success")

        except (NotFound, BusinessRuleError) as e:
            show_toast(self.frame, str(e), "error")

        except Exception:
            Messagebox.show_error("Error al eliminar uno o más movimientos", "error")

        finally:
            self._processing = False

    def _populate_table(self, filter: str = "Todo"):
        self.table.unload_table_data()

        if filter == FILTER_PAYMENTS:
            movements = [
                m for m in self._movements_cache if m.type == MovementType.PAYMENT
            ]
        elif filter == FILTER_FEES:
            movements = [m for m in self._movements_cache if m.type == MovementType.FEE]
        else:
            movements = self.s.cqrs.get_all_movements()

        self.table.build_table_data(
            ADMIN_MOVEMENTS_COLUMNS,
            [self._movement_to_row(movement) for movement in movements],
        )
        self.table.load_table_data()

    def refresh_table(self):
        self._movements_cache = self.s.cqrs.get_all_movements()

        current_filter = self.table_filters.get()
        self._populate_table(current_filter)

    def _on_filter_selected(self, _event=None):
        self._populate_table(self.table_filters.get())
