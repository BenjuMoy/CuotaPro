import logging
from dataclasses import dataclass
from sqlite3 import DatabaseError
from typing import Callable

import ttkbootstrap as ttk
from pydantic import BaseModel
from ttkbootstrap.dialogs import Messagebox

from domain.shared.exceptions import AppValidationError, ConflictError, NotFound
from ui.views.constants import PAD_X, PAD_Y
from ui.views.helpers_gui import (
    clear_inputs,
    clear_style,
    create_label_combobox,
    create_label_entry,
    enable_form_fields,
    mark_invalid,
)
from ui.views.toast import show_toast

# TODO Move form creation and validation to pydantic

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


@dataclass
class Section:
    title: str
    fields: list[FieldConfig]


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
        layout: list[Section],
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

        self.layout = layout

        self.form_fields: dict[str, ttk.Entry | ttk.Combobox] = {}
        self.field_meta: dict[str, FieldConfig] = {}

        self.readonly_fields: set[str] = set()

        self.form_frame = ttk.Labelframe(self.frame, text=form_title)
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.configure(style="Bold.TLabelframe")

        self.main_frame = ttk.Frame(self.frame)

        self.mapper = FormMapper(self.form_fields, self.field_meta, model_class)
        self.state = FormStateManager(self.form_fields, self.readonly_fields)
        self.actions = ActionHandler(self.frame)

    # --------------------------------------------------
    # FIELD CREATION
    # --------------------------------------------------

    def _create_fields_from_layout(self, column_index: int):
        """Create form fields from a declarative layout."""
        for section_idx, section in enumerate(self.layout):
            section_frame = ttk.Labelframe(
                self.form_frame, text=section.title, padding=10
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

            for idx, field in enumerate(section.fields):
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


# TODO Move to this class


class _BaseStudentFormTab:
    def __init__(self, parent, form_title, layout, model_class):
        self.frame = ttk.Frame(parent)
        self.form_frame = ttk.Labelframe(self.frame, text=form_title)

        builder = FormBuilder(self.form_frame, layout)
        self.form_fields, self.field_meta, self.readonly_fields = builder.build()

        self.validator = FormValidator(self.field_meta)
        self.mapper = FormMapper(self.field_meta, model_class)
        self.state = FormStateManager(self.form_fields)
        self.actions = ActionHandler(self.frame)


class FormBuilder:
    def __init__(self, parent, layout):
        self.parent = parent
        self.layout = layout

    def build(self):
        form_fields = {}
        field_meta = {}
        readonly_fields = set()

        for section_idx, section in enumerate(self.layout):
            section_frame = ttk.Labelframe(self.parent, text=section.title, padding=10)
            section_frame.grid(row=section_idx, column=0, sticky="nsew")

            for idx, field in enumerate(section.fields):
                widget = self._create_field(section_frame, field, idx)

                form_fields[field.name] = widget
                field_meta[field.name] = field

                if field.readonly:
                    readonly_fields.add(field.name)

        return form_fields, field_meta, readonly_fields

    def _create_field(self, parent, field, row):
        if field.type == ttk.Entry:
            return create_label_entry(...)
        return create_label_combobox(...)


class FormValidator:
    def __init__(self, field_meta):
        self.field_meta = field_meta

    def validate(self, form_fields):
        errors = []

        for name, widget in form_fields.items():
            meta = self.field_meta[name]
            value = widget.get().strip()

            if meta.required and not value:
                errors.append((name, f"Campo '{meta.label}' es obligatorio"))

            if meta.numeric and value and not value.isdigit():
                errors.append((name, f"Campo '{meta.label}' debe ser numérico"))

        if errors:
            raise AppValidationError("\n".join(msg for _, msg in errors))


# --------------------------------------------------
# DATA EXTRACTION
# --------------------------------------------------


class FormMapper:
    def __init__(
        self,
        fields: dict[str, ttk.Entry | ttk.Combobox],
        meta: dict[str, FieldConfig],
        model_class: type[BaseModel],
    ):
        self.fields = fields
        self.meta = meta
        self.model_class = model_class

    def to_model(self) -> BaseModel:
        data = {}

        for name, widget in self.fields.items():
            meta = self.meta.get(name)
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
            data["active"] = True  # FIXME

        try:
            return self.model_class(**data)
        except Exception as e:
            raise AppValidationError(str(e))

    # --------------------------------------------------
    # STATE MANAGEMENT
    # --------------------------------------------------


class FormStateManager:
    def __init__(
        self,
        form_fields: dict[str, ttk.Entry | ttk.Combobox],
        read_only_fields: set[str],
    ):
        self.fields = form_fields
        self.read_only = read_only_fields

    def set_form_state(self, enabled: bool = True):
        """Enables or disables all form entry widgets."""
        enable_form_fields(list(self.fields.values()), enabled)

    def set_readonly_fields(self):
        enable_form_fields([self.fields[f] for f in self.read_only], False)

    def clear_form(self):
        """Clears all text from form entry widgets."""
        clear_inputs(list(self.fields.values()))

    def clear_form_styles(self):
        """Removes any success/danger styling from form entry widgets."""
        clear_style(list(self.fields.values()))

    def reset_comboboxes(self):
        for widget in self.fields.values():
            if isinstance(widget, ttk.Combobox):
                widget.set("")

    def populate_form(self, data_object: BaseModel):
        """Populates the form fields with data from a Pydantic model instance."""
        self.clear_form()
        for attr_name, entry_widget in self.fields.items():
            value = getattr(data_object, attr_name, "")
            value = "" if value is None else value

            if hasattr(entry_widget, "set"):
                entry_widget.set(value)
            else:
                entry_widget.insert(0, str(value))


class _FormStateManager:
    def __init__(self, form_fields):
        self.form_fields = form_fields

    def clear(self):
        clear_inputs(list(self.form_fields.values()))

    def clear_styles(self):
        clear_style(list(self.form_fields.values()))

    def enable(self, enabled=True):
        enable_form_fields(list(self.form_fields.values()), enabled)

    def populate(self, data):
        for name, widget in self.form_fields.items():
            value = getattr(data, name, "") or ""
            if hasattr(widget, "set"):
                widget.set(value)
            else:
                widget.insert(0, str(value))


# --------------------------------------------------
# ACTION WRAPPER
# --------------------------------------------------


class ActionHandler:
    def __init__(self, frame: ttk.Frame):
        self.frame = frame

    def run(self, action_fn: Callable, success_msg: str):
        try:
            result = action_fn()
            show_toast(self.frame, success_msg, "success")
            return result

        except (
            ConflictError,
            NotFound,
            AppValidationError,
            DatabaseError,
            ValueError,
        ) as e:
            show_toast(self.frame, str(e), "error")

        except Exception as e:
            logger.exception("Unexpected error")
            Messagebox.show_error(str(e), "Error")
