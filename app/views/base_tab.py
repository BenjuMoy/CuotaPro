import logging
from dataclasses import dataclass
from sqlite3 import DatabaseError
from typing import Any, Callable, get_type_hints

import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pydantic import BaseModel
from ttkbootstrap.dialogs import Messagebox

from app.models.exceptions import (
    AppValidationError,
    ConflictError,
    NotFound,
)
from app.utils.constantes import FONT_TITLE, PAD_X, PAD_Y
from app.views.helpers_gui import (
    clear_inputs,
    clear_style,
    create_label_combobox,
    create_label_entry,
    enable_form_fields,
    mark_invalid,
)
from app.views.toast import show_toast
from app.views.widgets.kpi_card import KpiCard

logger = logging.getLogger()


@dataclass
class FieldConfig:
    name: str
    label: str
    type: type[ttk.Entry | ttk.Combobox]
    converter: type[str | int]
    required: bool = False
    focus: bool = False
    numeric: bool = False
    values: list[str] | None = None
    readonly: bool = False


class BaseStudentFormTab:
    """
    A base class for creating tabs that contain a form for a Pydantic model.

    This class handles the generic creation of form fields (labels and entries),
    as well as common actions like clearing, populating, and enabling/disabling
    the form.
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        form_title: str,
        layout: list[dict[str, Any]],
        model_class: type[BaseModel],
    ):
        """
        Initializes the BaseFormTab.

        Args:
            parent: The parent ttk.Notebook widget.
            tab_title: The title to display on the tab.
            form_title: The title for the Labelframe containing the form fields.
            model_class: The Pydantic model class this form is for (e.g., Estudiante).
        """
        self.frame = ttk.Frame(parent)

        self.model_class = model_class
        self.layout = layout

        self.form_fields: dict[str, ttk.Entry | ttk.Combobox] = {}
        self.field_meta: dict[str, FieldConfig] = {}

        self.readonly_fields: set[str] = set()

        self.form_frame = ttk.Labelframe(self.frame, text=form_title)
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.configure(style="Bold.TLabelframe")

        self.main_frame = ttk.Frame(self.frame)

    # --------------------------------------------------
    # FIELD CREATION
    # --------------------------------------------------

    def _create_fields_from_layout(self, column_index: int):
        """Create form fields from a declarative layout."""
        for section_idx, section in enumerate(self.layout):
            section_frame = ttk.Labelframe(
                self.form_frame, text=section["section"], padding=10
            )
            section_frame.grid(
                row=section_idx,
                column=column_index,
                sticky="nsew",
                padx=PAD_X,
                pady=PAD_Y,
            )
            section_frame.configure(style="Bold.TLabelframe")
            section_frame.columnconfigure(1, weight=1)

            for idx, field in enumerate(section["fields"]):
                widget = self._create_field(section_frame, field, idx)

                self.form_fields[field.name] = widget
                self.field_meta[field.name] = field

                if field.readonly:
                    self.readonly_fields.add(field.name)

    def _create_field(self, parent, field: FieldConfig, row: int):
        if field.type == ttk.Entry:
            return create_label_entry(
                parent,
                field.label,
                row,
                0,
                focus=field.focus,
                required=field.required,
            )
        else:
            return create_label_combobox(
                parent,
                field.label,
                row,
                0,
                values=field.values or [],
                required=field.required,
            )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def bind_required_validation(self):
        for name, widget in self.form_fields.items():
            meta = self.field_meta.get(name)
            if not meta:
                continue

            if meta.required:
                widget.bind("<FocusOut>", self._validate_widget)

            if meta.numeric:
                vcmd = (
                    self.frame.register(lambda P: P.isdigit() or P == ""),
                    "%P",
                )
                widget.config(validate="key", validatecommand=vcmd)

    def _validate_widget(self, event):
        widget = event.widget
        value = widget.get().strip()

        # Find field name
        name = next((k for k, v in self.form_fields.items() if v == widget), None)
        meta = self.field_meta.get(name)

        if not meta:
            return

        if meta.required and not value:
            mark_invalid(widget)
            return

        if meta.numeric and value and not value.isdigit():
            mark_invalid(widget)
            return

        clear_style([widget])

    def validate_form(self):
        error_messages = []

        for name, widget in self.form_fields.items():
            meta = self.field_meta.get(name)
            if not meta:
                continue

            value = widget.get().strip()

            if meta.required and not value:
                mark_invalid(widget)
                widget.focus_set()
                error_messages.append(f"Campo '{meta.label}' es obligatorio")

        if error_messages:
            raise AppValidationError("\n".join(error_messages))

    # --------------------------------------------------
    # DATA EXTRACTION
    # --------------------------------------------------

    def get_form_data(self) -> dict[str, str | int]:
        """Retrieves data from all form fields and returns it as a dictionary."""
        data = {}

        for name, widget in self.form_fields.items():
            meta = self.field_meta.get(name)
            if not meta:
                continue

            value = widget.get().strip()

            if meta.converter and value:
                try:
                    value = meta.converter(value)
                except Exception:
                    raise AppValidationError(
                        f"Campo '{meta.label}' tiene formato inválido"
                    )

            data[name] = value

        return data

    # --------------------------------------------------
    # STATE MANAGEMENT
    # --------------------------------------------------

    def set_form_state(self, enabled: bool = True):
        """Enables or disables all form entry widgets."""
        enable_form_fields(list(self.form_fields.values()), enabled)

    def set_readonly_fields(self):
        enable_form_fields([self.form_fields[f] for f in self.readonly_fields], False)

    def clear_form(self):
        """Clears all text from form entry widgets."""
        clear_inputs(list(self.form_fields.values()))

    def clear_form_styles(self):
        """Removes any success/danger styling from form entry widgets."""
        clear_style(list(self.form_fields.values()))

    def reset_comboboxes(self):
        for widget in self.form_fields.values():
            if isinstance(widget, ttk.Combobox):
                widget.set("")

    def populate_form(self, data_object: BaseModel):
        """Populates the form fields with data from a Pydantic model instance."""
        self.clear_form()
        for attr_name, entry_widget in self.form_fields.items():
            value = getattr(data_object, attr_name, "")
            value = "" if value is None else value

            if hasattr(entry_widget, "set"):
                entry_widget.set(value)
            else:
                entry_widget.insert(0, str(value))

    # --------------------------------------------------
    # ACTION WRAPPER
    # --------------------------------------------------

    def run_action(self, action_fn, success_msg):
        try:
            result = action_fn()
            show_toast(self.frame, success_msg, "success")
            return result

        except ConflictError as e:
            show_toast(self.frame, str(e), "error")

        except NotFound as e:
            show_toast(self.frame, f"Estudiante no encontrado: {e}", "error")

        except AppValidationError as e:
            show_toast(self.frame, str(e), "error")

        except DatabaseError as e:
            show_toast(self.frame, f"Error de base de datos: {e}", "error")

        except ValueError as e:
            show_toast(self.frame, f"ID inválido: {e}", "error")

        except Exception as e:
            logger.exception("Unexpected error in form action")
            Messagebox.show_error(
                f"Error inesperado.  Contacte al administrador: {e}", "Error"
            )


class BaseMetricsTab:
    def __init__(
        self,
        parent: ttk.Notebook,
        title: str,
        cards: dict[str, str],
    ):
        self.parent = parent
        self.frame = ttk.Frame(parent, padding=25)

        self.title = title
        self.kpi_config = cards

        self.cards: dict[str, KpiCard] = {}

        self.chart_style = "seaborn-v0_8"
        self.chart_frame: ttk.Frame | None = None

    # -------------------------
    # CARDS
    # -------------------------

    def create_kpi_cards(self):
        ttk.Label(
            self.frame,
            text=self.title,
            font=FONT_TITLE,
        ).pack(pady=15)

        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", pady=10)

        for i, (name, label) in enumerate(self.kpi_config.items()):
            card = KpiCard(self.kpi_frame, label)
            card.grid(row=0, column=i, padx=15, pady=10, sticky="nsew")

            self.kpi_frame.columnconfigure(i, weight=1)
            self.cards[name] = card

    # -------------------------
    # BUTTONS
    # -------------------------

    def build_buttons(self, buttons: dict[int, tuple[str, str]]):
        actions = ttk.Labelframe(
            self.frame,
            text="Acciones rápidas",
            padding=15,
        )
        actions.pack(fill="x", pady=15)

        for idx, (label, style) in buttons.items():
            ttk.Button(
                actions,
                text=label,
                bootstyle=style,
                command=lambda tab_index=idx: self.parent.select(tab_index),
            ).pack(side="left", padx=10, pady=10, expand=True, fill="x")

    # -------------------------
    # CHARTS
    # -------------------------

    def draw_charts(
        self,
        income_by_month: dict,
        teacher_count: dict,
        debt_bucket: dict,
    ):
        if self.chart_frame is None:
            self.chart_frame = ttk.Frame(self.frame)
            self.chart_frame.pack(fill="both", expand=True)

        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        plt.style.use(self.chart_style)

        fig = plt.figure(figsize=(10, 6))
        gs = fig.add_gridspec(2, 2)

        self._draw_income_chart(fig.add_subplot(gs[0, :]), income_by_month)
        self._draw_teacher_chart(fig.add_subplot(gs[1, 0]), teacher_count)
        self._draw_debt_chart(fig.add_subplot(gs[1, 1]), debt_bucket)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        plt.close(fig)

    # -------------------------
    # CHARTS IMPLEMENTATION
    # -------------------------

    def _draw_income_chart(self, ax: Axes, data: dict):
        ax.bar(list(data.keys()), list(data.values()))
        ax.set_title("Ingresos últimos 6 meses")
        ax.tick_params(axis="x", rotation=45)

    def _draw_teacher_chart(self, ax: Axes, data: dict):
        ax.barh(list(data.keys()), list(data.values()))
        ax.set_title("Estudiantes por Profesor")

    def _draw_debt_chart(self, ax: Axes, data: dict):
        values = list(data.values())
        labels = list(data.keys())

        total = sum(values)

        if total == 0:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
            return

        colors = ["green", "gold", "orange", "red"][: len(values)]

        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
        )

        ax.set_title("Estado de Pagos")
