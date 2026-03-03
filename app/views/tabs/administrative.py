from datetime import datetime

import ttkbootstrap as ttk
from ttkbootstrap.constants import DANGER
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.controllers.main_controller import AppController
from app.models.exceptions import BusinessRuleError, NotFound
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
from app.views.helpers_gui import (
    clear_inputs,
    clear_style,
    create_label_combobox,
    create_label_entry,
    create_label_frame,
)
from app.views.toast import show_toast

FILTER_ALL = "Todo"
FILTER_PAYMENTS = "Pagos"
FILTER_FEES = "Cuotas"


class AdministrativeTab:
    def __init__(self, parent: ttk.Notebook, controller: AppController):
        self.controller: AppController = controller
        self.frame: ttk.Frame = ttk.Frame(parent)
        self._processing = False

        self.controller.subscribe(self.refresh_results)

        self._create_widgets()
        self._create_movement_list()

    # GUI creation

    def _create_widgets(self):
        # Aplicar cuotas Frame
        aplicar_cuotas_frame = ttk.Labelframe(
            self.frame, text="Aplicar Cuotas Mensuales"
        )
        aplicar_cuotas_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)
        aplicar_cuotas_frame.configure(style="Bold.TLabelframe")

        ttk.Label(
            aplicar_cuotas_frame,
            text="⚠ Acción global masiva. Se generará un cargo para cada alumno activo.",
            bootstyle="danger",
            font=("TkDefaultFont", 11, "bold"),
        ).grid(row=0, column=0, padx=PAD_X, pady=PAD_Y)

        self.apply_fees_button: ttk.Button = ttk.Button(
            aplicar_cuotas_frame,
            text="Aplicar Cuotas",
            command=self.apply_monthly_fees,
            bootstyle=DANGER,
        )
        self.apply_fees_button.grid(
            row=1, column=0, columnspan=2, padx=PAD_X, pady=PAD_Y
        )

        if not self.controller.fees_not_applied_for_period():
            self.apply_fees_button.config(state="disabled")

        data = self.controller.get_fees_list()

        date = self.controller.get_last_applied_fees_date()

        if date:
            last_month = date[0]
            last_year = date[1]
            text = f"Ultima fecha aplicada: {NUM_TO_MONTH[last_month]} de {last_year}"
        else:
            last_month = "Ningun mes"
            last_year = "Ningun año"
            text = f"Ultima fecha aplicada: {last_month} de {last_year}"

        self.aplicar_cuotas_label: ttk.Label = ttk.Label(
            aplicar_cuotas_frame,
            text=text,
            font=FONT_BODY,
        )
        self.aplicar_cuotas_label.grid(row=2, column=0, padx=PAD_X, pady=PAD_Y)

        # Aumentar cuotas frame
        aumentar_cuotas_frame = ttk.Labelframe(
            self.frame, text="Aumentar Valor De Cuotas"
        )
        aumentar_cuotas_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)
        aumentar_cuotas_frame.configure(style="Bold.TLabelframe")

        values = [f"{value[0]} ({value[1]})" for value in data]

        # Boton para aumentar las cuotas
        self.old_monthly_fee_combo: ttk.Combobox = create_label_combobox(
            aumentar_cuotas_frame, "Cuota actual ($)", 0, 0, values, False
        )

        self.new_monthly_fee_entry: ttk.Entry = create_label_entry(
            aumentar_cuotas_frame,
            "Nueva cuota ($)",
            1,
            0,
        )

        # Boton para aumentar cuotas
        self.increase_fee_button: ttk.Button = ttk.Button(
            aumentar_cuotas_frame,
            text="Aumentar Valor De Cuotas",
            command=self.increase_fee_amount,
        )
        self.increase_fee_button.grid(row=5, column=0, columnspan=2, pady=PAD_Y)

        for entry in (self.old_monthly_fee_combo, self.new_monthly_fee_entry):
            vcmd = (self.frame.register(lambda P: P.isdigit() or P == ""), "%P")
            entry.config(validate="key", validatecommand=vcmd)

    def _create_movement_list(self):
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

        # Define columns
        columnas = (
            CAMPO_ID,
            "ID del estudiante",
            "Tipo",
            "Monto",
            "Mes",
            "Año",
            "Fecha pagada",
        )

        rows = []

        self.table: Tableview = Tableview(
            self.filter_frame,
            searchable=True,
            coldata=columnas,
            rowdata=rows,
            yscrollbar=True,
        )

        self.table.pack(expand=True, padx=PAD_X, pady=PAD_Y, fill="both")

        self.table_filters.bind("<<ComboboxSelected>>", self._on_filter_selected)
        self.table.view.bind("<Double-1>", self.on_double_click)

        self._populate_movements_table(self.table_filters.get())

    # Action Functions

    def _parse_positive_int(self, value: str) -> int | None:
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _on_filter_selected(self, event=None):
        self._populate_movements_table(self.table_filters.get())

    def _set_processing(self, value: bool):
        self._processing = value
        state = (
            "disabled"
            if not self.controller.fees_not_applied_for_period()
            else "normal"
        )
        self.apply_fees_button.config(
            state=state, text="Procesando..." if value else "Aplicar Cuotas"
        )
        self.increase_fee_button.config(
            state=state, text="Procesando..." if value else "Aumentar Valor De Cuotas"
        )
        self.frame.config(cursor="watch" if value else "")
        self.frame.update_idletasks()

    def apply_monthly_fees(self) -> None:
        active_students: int = self.controller.get_active_student_count()
        now = datetime.now()

        confirm = Messagebox.yesno(
            (
                f"""Fecha {NUM_TO_MONTH[now.month]} {now.year}. \nAlumnos activos {active_students} \n¿Desea continuar?"""
            ),
            "Confirmar Aplicación",
        )

        if confirm != "Yes":
            return

        try:
            self._set_processing(True)

            affected_count = self.controller.apply_monthly_fees()

            show_toast(
                self.frame,
                f"Cuotas aplicadas a {affected_count} alumnos",
                "success",
            )

            self._refresh_apply_label()
            self.apply_fees_button.config(state="disabled")

        except NotFound:
            show_toast(self.frame, "No se aplico ninguna cuota", "error")
            self.apply_fees_button.config(state="normal")
        except BusinessRuleError as e:
            show_toast(self.frame, f"Error: {str(e)}", "error")
            self.apply_fees_button.config(state="normal")
        except Exception:
            self.controller.logger.exception("Failed to apply monthly fees")
            show_toast(self.frame, "Error al aplicar cuotas", "error")
            self.apply_fees_button.config(state="normal")
        finally:
            self._set_processing(False)
            # self.apply_fees_button.config(state="disabled")

    def _refresh_apply_label(self):
        date = self.controller.get_last_applied_fees_date()
        if not date:
            text = "No se aplicaron cuotas todavía"
        else:
            text = f"Última fecha aplicada: {NUM_TO_MONTH.get(date[0], 'N/A')} de {date[1]}"
        self.aplicar_cuotas_label.config(text=text)

    # Funcion para aumentar cuotas
    def increase_fee_amount(self):
        if self._processing:
            return

        old_monthly_fee_str = self.old_monthly_fee_combo.get().split()[0]

        old_monthly_fee = self._parse_positive_int(old_monthly_fee_str)
        if old_monthly_fee is None:
            show_toast(self.frame, "Ingrese una cuota válida", "error")
            return
        affected = self.controller.count_students_by_monthly_fee(old_monthly_fee)

        if not affected:
            self.old_monthly_fee_combo.configure(style="danger.TEntry")
            show_toast(
                self.frame, "No se encontraron estudiantes con esa cuota", "error"
            )
            return None

        new_monthly_fee = self._parse_positive_int(self.new_monthly_fee_entry.get())
        if new_monthly_fee is None:
            show_toast(self.frame, "Ingrese una cuota válida", "error")
            return

        if old_monthly_fee >= new_monthly_fee:
            show_toast(self.frame, "La nueva cuota debe ser mayor", "error")
            return

        confirm = Messagebox.yesno(
            f"""Cambiar cuota:\n
            {currency_format(old_monthly_fee)} -> {currency_format(new_monthly_fee)}

            Afectará a {affected} alumnos.
            ¿Desea continuar?""",
            "Confirmar Cambios",
        )

        if confirm != "Yes":
            return

        try:
            self._set_processing(True)

            updated_count = self.controller.increase_fee_amount(
                old_monthly_fee, new_monthly_fee
            )

            show_toast(
                self.frame,
                f"Se aumentaron las cuotas a {updated_count} alumnos",
                "success",
            )

            clear_inputs([self.old_monthly_fee_combo, self.new_monthly_fee_entry])
            clear_style([self.old_monthly_fee_combo, self.new_monthly_fee_entry])

        except BusinessRuleError as e:
            show_toast(self.frame, f"Error: {str(e)}", "error")

        except Exception:
            self.controller.logger.exception("Fee increase failed")
            show_toast(self.frame, "Error al actualizar cuotas", "error")

        finally:
            self._set_processing(False)

    def on_double_click(self, event):
        if self._processing:
            return
        selected_rows = self.table.get_rows(selected=True)
        if not selected_rows:
            return

        row_values = selected_rows[0].values

        if len(selected_rows) == 1:
            res = Messagebox.yesno(
                f"ID del alumno: {row_values[1]} \nTipo: {row_values[2]} \nFecha: {row_values[6]} \nMonto: {row_values[3]}",
                "Reverir movimiento",
            )
        else:
            res = Messagebox.yesno(
                "Esta seguro que desea revertir los movimientos seleccionados?",
                "Revertir movimientos",
            )

        if res != "Yes":
            show_toast(self.frame, "No se revirtio el movimiento", "warn")
            return

        try:
            for row_data in selected_rows:
                pago_id = row_data.values[0]
                self.controller.reverse_movement(pago_id)

            show_toast(self.frame, "Movimiento revertido", "success")
            self.refresh_results()

        except BusinessRuleError as e:
            show_toast(self.frame, str(e), "error")

        except NotFound as e:
            show_toast(self.frame, str(e), "error")

        except Exception:
            show_toast(self.frame, "Error al eliminar uno o más movimientos", "error")

    def _populate_movements_table(self, filter: str = "Todo"):
        self.table.delete_rows()

        if filter == FILTER_PAYMENTS:
            movements = self.controller.get_effective_payments()
        elif filter == FILTER_FEES:
            movements = self.controller.get_effective_fees()
        else:
            movements = self.controller.get_all_movements()

        for mov in movements:
            data = (
                mov.id,
                mov.student_id,
                TYPE_TRANSLATE[mov.type],
                currency_format(mov.amount),
                NUM_TO_MONTH[mov.month],
                mov.year,
                mov.created_at.strftime(FECHA_HOY_AHORA_FMT),
            )
            self.table.insert_row("end", data)

    def refresh_results(self):
        current_filter = self.table_filters.get()
        self._populate_movements_table(current_filter)

        data = self.controller.get_fees_list()
        self.old_monthly_fee_combo.config(
            values=[f"{value[0]} ({value[1]})" for value in data]
        )
