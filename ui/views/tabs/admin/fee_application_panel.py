import logging
from datetime import datetime

import ttkbootstrap as ttk
from pydantic import ValidationError
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.style import DANGER

from bootstrap.containers import ServiceContainer
from domain.shared.exceptions import NotFound
from ui.views.constants import FONT_BODY, FONT_HEADER, NUM_TO_MONTH, PAD_X, PAD_Y
from ui.views.toast import show_toast

logger = logging.getLogger()


class FeeApplicationPanel:
    def __init__(self, frame: ttk.Frame, services: ServiceContainer):
        self.frame = frame
        self._processing = False

        self.s = services

        self._create_widgets()

    def _create_widgets(self):
        # Aplicar cuotas Frame
        aplicar_cuotas_frame = ttk.Labelframe(
            self.frame, text="Aplicar Cuotas Mensuales"
        )
        aplicar_cuotas_frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)
        aplicar_cuotas_frame.configure(style="Bold.TLabelframe")

        ttk.Label(
            aplicar_cuotas_frame,
            text="⚠ Acción global masiva.\n Se generará un cargo para cada alumno activo y sin cuota aplicada.",
            bootstyle="danger",
            # font=("TkDefaultFont", 11, "bold"),
            font=(FONT_HEADER),
        ).grid(row=0, column=0, padx=PAD_X, pady=PAD_Y)

        self.apply_fees_button = ttk.Button(
            aplicar_cuotas_frame,
            text="Aplicar Cuotas",
            command=self.apply_monthly_fees,
            bootstyle=DANGER,
        )
        self.apply_fees_button.grid(
            row=1, column=0, columnspan=2, padx=PAD_X, pady=PAD_Y
        )

        period = self.s.cqrs.get_last_fee_date()

        if period:
            text = f"Ultimo periodo aplicado: {NUM_TO_MONTH[period.month]} de {period.year}"
        else:
            text = "Ultimo periodo aplicado: Ningun mes de Ningun año "

        self.aplicar_cuotas_label: ttk.Label = ttk.Label(
            aplicar_cuotas_frame,
            text=text,
            font=FONT_BODY,
        )
        self.aplicar_cuotas_label.grid(row=2, column=0, padx=PAD_X, pady=PAD_Y)

    def apply_monthly_fees(self) -> None:
        if self._processing:
            return

        now = datetime.now()
        count = self.s.cqrs.preview_fee_application(now.month, now.year)

        confirm = Messagebox.yesno(
            (
                f"""⚠ Acción irreversible

Periodo: {NUM_TO_MONTH[now.month]} {now.year}
Alumnos afectados: {count}

Se generarán cargos automáticamente.

¿Confirmar?"""
            ),
            "Confirmar Aplicación",
        )

        if confirm != "Yes":
            return

        try:
            self._set_processing(True)

            affected_count = self.s.accounting.add_fee(now.month, now.year)

            show_toast(
                self.frame,
                f"Cuotas aplicadas a {affected_count} alumnos",
                "success",
            )

            self._refresh_apply_label()

        except (ValidationError, NotFound) as e:
            show_toast(self.frame, f"Error: {e}", "error")
            self.apply_fees_button.config(state="normal")

        except Exception:
            logger.exception("Failed to apply monthly fees")
            self.apply_fees_button.config(state="normal")
            Messagebox.show_error("Error al aplicar cuotas", "error")

        finally:
            self._set_processing(False)
            self._update_button_state()

    def _refresh_apply_label(self):
        period = self.s.cqrs.get_last_fee_date()
        if not period:
            text = "No se aplicaron cuotas todavía"
        else:
            text = f"Último periodo aplicado: {NUM_TO_MONTH.get(period.month, 'N/A')} de {period.year}"
        self.aplicar_cuotas_label.config(text=text)

    def _set_processing(self, value: bool):
        self._processing = value
        state = "disabled" if value else "normal"
        self.apply_fees_button.config(
            state=state, text="Procesando..." if value else "Aplicar Cuotas"
        )
        self.frame.config(cursor="watch" if value else "")
        self.frame.update_idletasks()

    def _update_button_state(self):
        enabled = self.s.cqrs.are_fees_applied()
        self.apply_fees_button.config(state="normal" if enabled else "disabled")
