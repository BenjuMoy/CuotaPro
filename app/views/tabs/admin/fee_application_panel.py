from datetime import datetime

import ttkbootstrap as ttk
from pydantic import ValidationError
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.style import DANGER

from app.models.exceptions import NotFound
from app.services.application_service import ApplicationService
from app.utils.constantes import FONT_BODY, FONT_HEADER, NUM_TO_MONTH, PAD_X, PAD_Y
from app.views.toast import show_toast


class FeeApplicationPanel:
    def __init__(self, frame: ttk.Frame, service: ApplicationService):
        self.frame = frame
        self._processing = False

        self.main_service = service

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

        if not self.main_service.fees_not_applied_for_period():
            self.apply_fees_button.config(text="Aplicar cuotas nuevamente")

        date = self.main_service.get_last_applied_fees_date()

        if date:
            text = f"Ultimo periodo aplicado: {NUM_TO_MONTH[date[0]]} de {date[1]}"
        else:
            text = "Ultimo periodo aplicado: Ningun mes de Ningun año "

        self.aplicar_cuotas_label: ttk.Label = ttk.Label(
            aplicar_cuotas_frame,
            text=text,
            font=FONT_BODY,
        )
        self.aplicar_cuotas_label.grid(row=2, column=0, padx=PAD_X, pady=PAD_Y)

    def apply_monthly_fees(self) -> None:
        now = datetime.now()
        student_list = self.main_service.get_students_without_fee(now.month, now.year)

        confirm = Messagebox.yesno(
            (
                f"""Periodo: {NUM_TO_MONTH[now.month]} {now.year}. \nCuotas a generar: {len(student_list)} \n¿Desea continuar?"""
            ),
            "Confirmar Aplicación",
        )

        if confirm != "Yes":
            return

        try:
            self._set_processing(True)

            affected_count = self.main_service.apply_monthly_fees()

            show_toast(
                self.frame,
                f"Cuotas aplicadas a {affected_count} alumnos",
                "success",
            )

            self._refresh_apply_label()
            self.apply_fees_button.config(state="disabled")

        except (ValidationError, NotFound) as e:
            show_toast(self.frame, f"Error: {e}", "error")
            self.apply_fees_button.config(state="normal")

        except Exception:
            self.main_service.logger.exception("Failed to apply monthly fees")
            self.apply_fees_button.config(state="normal")
            Messagebox.show_error("Error al aplicar cuotas", "error")

        finally:
            self._set_processing(False)
            if not self.main_service.fees_not_applied_for_period():
                self.apply_fees_button.config(state="disabled")

    def _refresh_apply_label(self):
        date = self.main_service.get_last_applied_fees_date()
        if not date:
            text = "No se aplicaron cuotas todavía"
        else:
            text = f"Último periodo aplicado: {NUM_TO_MONTH.get(date[0], 'N/A')} de {date[1]}"
        self.aplicar_cuotas_label.config(text=text)

    def _set_processing(self, value: bool):
        self._processing = value
        state = "disabled" if value else "normal"
        self.apply_fees_button.config(
            state=state, text="Procesando..." if value else "Aplicar Cuotas"
        )
        self.frame.config(cursor="watch" if value else "")
        self.frame.update_idletasks()
