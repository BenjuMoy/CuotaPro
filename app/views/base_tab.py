import logging
from sqlite3 import DatabaseError
from typing import Any, Callable, get_type_hints

import ttkbootstrap as ttk
from pydantic import ValidationError
from ttkbootstrap.dialogs import Messagebox

from app.models.models import (
    BaseModel,
)
from app.services.application_service import (
    AppValidationError,
    ConflictError,
    NotFound,
)
from app.utils.constantes import PAD_X, PAD_Y
from app.views.helpers_gui import (
    clear_inputs,
    clear_style,
    create_label_combobox,
    create_label_entry,
    enable_form_fields,
    mark_invalid,
)
from app.views.toast import show_toast

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
        self.field_meta = {}

        self.form_frame = ttk.Labelframe(self.frame, text=form_title)
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.configure(style="Bold.TLabelframe")

        # self.section_labels: dict[str, ttk.Label] = {}
        self.readonly_fields: set[str] = set()

        self.main_frame = ttk.Frame(self.frame)
        # self.main_frame.pack(fill="both", expand=False)

    # --------------------------------------------------
    # FIELD CREATION
    # --------------------------------------------------

    def _create_fields_from_layout(self, column_index: int):
        """Create form fields from a declarative layout."""
        for idx, section_config in enumerate(self.layout):
            section_frame = ttk.Labelframe(
                self.form_frame, text=section_config["section"]
            )
            section_frame.grid(
                row=idx,
                column=column_index,
                sticky="nsew",
                padx=PAD_X,
                pady=PAD_Y,
            )
            section_frame.configure(style="Bold.TLabelframe")
            section_frame.configure(padding=15)
            section_frame.columnconfigure(1, weight=1)

            for idx, field_config in enumerate(section_config["fields"]):
                if field_config["type"] == "entry":
                    self.create_entry_field(
                        section_frame,
                        field_config["name"],
                        field_config["label"],
                        idx,
                        required=field_config.get("required", False),
                        focus=field_config.get("focus", False),
                    )
                    self.field_meta[field_config["name"]] = field_config
                elif field_config["type"] == "combobox":
                    self.create_combobox_field(
                        section_frame,
                        field_config["name"],
                        field_config["label"],
                        field_config["values"],
                        idx,
                        required=field_config.get("required", False),
                    )
                    self.field_meta[field_config["name"]] = field_config
                if field_config.get("readonly"):
                    self.readonly_fields.add(field_config["name"])

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
                if field.get("required", False):
                    widget = self.form_fields.get(field["name"])
                    if widget:
                        widget.bind("<FocusOut>", self._validate_widget)
                        if field.get("numeric", False):
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

        for name, widget in reversed(self.form_fields.items()):
            meta = self.field_meta.get(name, {})
            if meta.get("required") and not widget.get():
                mark_invalid(widget)
                widget.focus_set()
                error_messages.append(f"Campo '{meta['label']}': No puede estar vacio")

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

            converter = meta.get("converter")

            if converter and value != "":
                try:
                    value = converter(value)
                except Exception:
                    raise AppValidationError(f"Campo '{name}' tiene formato inválido")

            # if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Combobox):
            #    data[name] = widget.get().strip()

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
            logger.error(f"Unexpected error in add_student: {e}")
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
            if attr_name == "teacher" or attr_name == "book":  # FIXME
                entry_widget.set(value)
            else:
                entry_widget.insert(0, "" if value is None else str(value))
            # if isinstance(entry_widget, ttk.Entry):
            #    entry_widget.insert(0, "" if value is None else str(value))
            # else:
            #    entry_widget.set(value)

    def clear_form(self):
        """Clears all text from form entry widgets."""
        entries = list(self.form_fields.values())
        clear_inputs(entries)

    def clear_form_styles(self):
        """Removes any success/danger styling from form entry widgets."""
        entries = list(self.form_fields.values())
        clear_style(entries)
