import logging
from sqlite3 import DatabaseError
from typing import Callable, get_type_hints

import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pydantic import ValidationError
from ttkbootstrap.dialogs import Messagebox

from app.models.models import (
    BaseModel,
    FieldConfig,
)
from app.services.application_service import (
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

logger = logging.getLogger(__name__)


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
        layout: list[dict[str, str | FieldConfig]],
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
        self.field_meta = {}

        self.form_frame = ttk.Labelframe(self.frame, text=form_title)
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.configure(style="Bold.TLabelframe")

        self.readonly_fields: set[str] = set()

        self.main_frame = ttk.Frame(self.frame)

    # --------------------------------------------------
    # FIELD CREATION
    # --------------------------------------------------

    def _create_fields_from_layout(self, column_index: int):
        """Create form fields from a declarative layout."""
        for section_idx, section_config in enumerate(self.layout):
            section_frame = ttk.Labelframe(
                self.form_frame, text=section_config["section"]
            )
            section_frame.grid(
                row=section_idx,
                column=column_index,
                sticky="nsew",
                padx=PAD_X,
                pady=PAD_Y,
            )
            section_frame.configure(style="Bold.TLabelframe")
            section_frame.configure(padding=15)
            section_frame.columnconfigure(1, weight=1)

            for field_idx, field_config in enumerate(section_config["fields"]):
                if field_config.type == ttk.Entry:
                    self.create_entry_field(
                        section_frame,
                        field_config.name,
                        field_config.label,
                        field_idx,
                        required=field_config.required,
                        focus=field_config.focus,
                    )
                    self.field_meta[field_config.name] = field_config
                else:
                    self.create_combobox_field(
                        section_frame,
                        field_config.name,
                        field_config.label,
                        field_config.values,
                        field_idx,
                        required=field_config.required,
                    )
                    self.field_meta[field_config.name] = field_config
                if field_config.readonly:
                    self.readonly_fields.add(field_config.name)

    def create_entry_field(self, parent, attr_name, label, row, **kwargs):
        entry = create_label_entry(
            parent=parent,
            text=label,
            row=row,
            column=0,
            **kwargs,
        )
        self.form_fields[attr_name] = entry
        return entry

    def create_combobox_field(
        self, parent, attr_name: str, label: str, values: list[str], idx, **kwargs
    ):
        cb = create_label_combobox(
            parent=parent,
            text=label,
            row=idx,
            column=0,
            values=values,
            **kwargs,
        )
        self.form_fields[attr_name] = cb

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def build_model(self):
        data = self.get_form_data()

        try:
            return self.model_class(**data)

        except ValidationError as e:
            raise AppValidationError(str(e))

    def bind_required_validation(self):
        for section in self.layout:
            for field in section["fields"]:
                if field.required:
                    widget = self.form_fields.get(field.name)
                    if widget:
                        widget.bind("<FocusOut>", self._validate_widget)
                        if field.numeric:
                            vcmd = (
                                self.frame.register(lambda P: P.isdigit() or P == ""),
                                "%P",
                            )
                            widget.config(validate="key", validatecommand=vcmd)

    def _validate_widget(self, event):
        widget = event.widget
        if not widget.get().strip():
            mark_invalid(widget)
        else:
            clear_style([widget])

    def validate_form(self):
        error_messages = []

        for name, widget in self.form_fields.items():
            meta = self.field_meta.get(name, {})
            if meta.required and not widget.get():
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
            value = widget.get().strip()
            meta = self.field_meta.get(name, {})

            converter = meta.converter

            if converter and value != "":
                try:
                    value = converter(value)
                except Exception:
                    raise AppValidationError(f"Campo '{name}' tiene formato inválido")

            data[name] = value

        return data

    def set_readonly_fields(self):
        enable_form_fields([self.form_fields[f] for f in self.readonly_fields], False)

    # --------------------------------------------------
    # ACTION WRAPPER
    # --------------------------------------------------

    def _run_action(self, action_fn, success_msg):
        try:
            result = action_fn()
            show_toast(self.frame, success_msg, "success")
            return result
        except ConflictError as e:
            show_toast(self.frame, str(e), "error")
        except NotFound as e:
            show_toast(self.frame, f"Estudiante no encontrado: {e}", "error")
            self.form_fields["last_name"].focus_set()
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

    # --------------------------------------------------
    # STATE MANAGEMENT
    # --------------------------------------------------

    def set_form_state(self, enabled: bool = True):
        """Enables or disables all form entry widgets."""
        entries = list(self.form_fields.values())
        enable_form_fields(entries, enabled)

    def populate_form(self, data_object: BaseModel):
        """Populates the form fields with data from a Pydantic model instance."""
        self.clear_form()
        for attr_name, entry_widget in self.form_fields.items():
            value = getattr(data_object, attr_name, "")
            if value is None:
                value = ""
            if hasattr(entry_widget, "set"):
                entry_widget.set(value)
            else:
                entry_widget.insert(0, "" if value is None else str(value))

    def clear_form(self):
        """Clears all text from form entry widgets."""
        entries = list(self.form_fields.values())
        clear_inputs(entries)

    def clear_form_styles(self):
        """Removes any success/danger styling from form entry widgets."""
        entries = list(self.form_fields.values())
        clear_style(entries)


class BaseMetricsTab:
    def __init__(
        self,
        parent: ttk.Notebook,
        title: str,
        cards: dict[str, str],
    ):
        self.parent = parent
        self.frame = ttk.Frame(parent, padding=25)
        self.kpi_config = cards
        self.title = title

        self.chart_style = "seaborn-v0_8"

        self.cards: dict[str, KpiCard] = {}

    # -------------------------
    # CARDS
    # -------------------------

    def create_kpi_cards(self):
        ttk.Label(self.frame, text=self.title, font=FONT_TITLE).pack(padx=20, pady=20)

        # KPIs
        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", padx=20, pady=20)

        for i, (name, label) in enumerate(self.kpi_config.items()):
            card = KpiCard(self.kpi_frame, label)
            card.grid(row=0, column=i, padx=20, pady=20, sticky="nsew")

            self.kpi_frame.columnconfigure(i, weight=1)
            self.kpi_frame.rowconfigure(0, weight=1)
            self.cards[name] = card

    # -------------------------
    # BUTTONS
    # -------------------------

    def build_buttons(self, buttons: dict[int, tuple[str, str]]):
        # Quick actions
        actions = ttk.Labelframe(
            self.frame,
            text="Acciones rápidas",
            padding=15,
        )
        actions.pack(fill="x", padx=20, pady=20)

        for idx, (label, style) in buttons.items():
            ttk.Button(
                actions,
                text=label,
                bootstyle=style,
                command=lambda i=idx: self.parent.select(i),
            ).pack(side="left", padx=20, pady=20, expand=True, fill="both")

    # -------------------------
    # CHARTS
    # -------------------------

    def draw_charts(
        self,
        income_by_month: dict[str, int],
        teacher_count: dict[str, int],
        debt_bucket: dict[str, int],
    ):
        if not hasattr(self, "chart_frame"):
            self.chart_frame = ttk.Frame(self.frame)
            self.chart_frame.pack(fill="both", expand=True)

        plt.style.use(self.chart_style)

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

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
    # Income last 6 months
    # -------------------------

    def _draw_income_chart(self, income_ax: Axes, income_by_month: dict[str, int]):
        income_ax.bar(list(income_by_month.keys()), list(income_by_month.values()))
        income_ax.set_title("Ingresos últimos 6 meses")
        income_ax.tick_params(axis="x", rotation=45)

    # -------------------------
    # Students per teacher
    # -------------------------

    def _draw_teacher_chart(self, teacher_ax: Axes, teacher_count: dict[str, int]):
        teacher_ax.barh(list(teacher_count.keys()), list(teacher_count.values()))
        teacher_ax.set_title("Estudiantes por Profesor")

    # -------------------------
    # Payment status
    # -------------------------

    def _draw_debt_chart(self, debt_ax: Axes, debt_buckets: dict[str, int]):
        values = list(debt_buckets.values())
        labels = list(debt_buckets.keys())

        colors = ["green", "gold", "orange", "red"]

        total = sum(values)

        if total == 0:
            debt_ax.text(
                0.5,
                0.5,
                "Sin datos",
                ha="center",
                va="center",
                fontsize=12,
            )

        else:
            debt_ax.pie(
                values,
                labels=labels,
                colors=colors,
                autopct="%1.0f%%",
            )

        debt_ax.set_title("Estado de Pagos")
