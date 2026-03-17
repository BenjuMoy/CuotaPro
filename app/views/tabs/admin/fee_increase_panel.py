import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from app.models.exceptions import BusinessRuleError, NotFound
from app.services.application_service import ApplicationService
from app.utils.constantes import PAD_X, PAD_Y
from app.utils.helpers import currency_format
from app.views.helpers_gui import (
    clear_inputs,
    clear_style,
    create_label_combobox,
    create_label_entry,
)
from app.views.toast import show_toast


class FeeIncreasePanel:
    def __init__(self, frame: ttk.Frame, service: ApplicationService):
        self.frame = frame
        self._processing = False

        self.main_service = service

        self.fee_map = {}

        self._create_widgets()

    def _create_widgets(self):
        fees = self.main_service.get_fees_list()

        # Aumentar cuotas frame
        aumentar_cuotas_frame = ttk.Labelframe(
            self.frame, text="Aumentar Valor De Cuotas"
        )
        aumentar_cuotas_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)
        aumentar_cuotas_frame.configure(style="Bold.TLabelframe")

        # values = [f"{value[0]} ({value[1]})" for value in data]

        values = []

        for fee, count in fees:
            label = f"{fee} ({count} alumnos)"

            values.append(label)
            self.fee_map[label] = fee

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

        # Set new monthly fee entry to numbers only
        vcmd = (self.frame.register(lambda P: P.isdigit() or P == ""), "%P")
        self.new_monthly_fee_entry.config(validate="key", validatecommand=vcmd)

    # Static Methods

    def increase_fee_amount(self):
        if self._processing:
            return

        # old_monthly_fee_str = self.old_monthly_fee_combo.get().split()[0]
        # old_monthly_fee = self._parse_positive_int(old_monthly_fee_str)

        selected_label = self.old_monthly_fee_combo.get()
        old_monthly_fee = self.fee_map.get(selected_label)

        if old_monthly_fee is None:
            show_toast(self.frame, "Ingrese una cuota válida", "error")
            return
        affected = self.main_service.count_students_by_monthly_fee(old_monthly_fee)

        new_monthly_fee = int(self.new_monthly_fee_entry.get())
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

            updated_count = self.main_service.increase_fee_amount(
                old_monthly_fee, new_monthly_fee
            )

            show_toast(
                self.frame,
                f"Se aumentaron las cuotas a {updated_count} alumnos",
                "success",
            )

            clear_inputs([self.old_monthly_fee_combo, self.new_monthly_fee_entry])
            clear_style([self.old_monthly_fee_combo, self.new_monthly_fee_entry])

            self.refresh_fee_combo()

        except (NotFound, BusinessRuleError) as e:
            show_toast(self.frame, f"Error: {str(e)}", "error")

        except Exception as e:
            self.main_service.logger.exception("Fee increase failed")
            show_toast(self.frame, f"Error al actualizar cuotas: {e}", "error")

        finally:
            self._set_processing(False)

    def _set_processing(self, value: bool):
        self._processing = value
        state = "disabled" if value else "normal"
        self.increase_fee_button.config(
            state=state, text="Procesando..." if value else "Aumentar Valor De Cuotas"
        )
        self.frame.config(cursor="watch" if value else "")
        self.frame.update_idletasks()

    def refresh_fee_combo(self):
        data = self.main_service.get_fees_list()
        self.old_monthly_fee_combo.config(
            values=[f"{value[0]} ({value[1]})" for value in data]
        )
        self.old_monthly_fee_combo.set("")
