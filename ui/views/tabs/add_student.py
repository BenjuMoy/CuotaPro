import ttkbootstrap as ttk

from application.dto import CreateStudentDTO
from bootstrap.containers import ServiceContainer
from domain.shared.exceptions import AppValidationError
from ui.views.base_tabs.student_form import BaseStudentFormTab, FieldConfig, Section
from ui.views.constants import BOOKS, COURSES, ICON_ADD, PAD_X, PAD_Y, TEACHERS, YEAR
from ui.views.toast import show_toast

FORM_LAYOUT = [
    Section(
        title="Identidad",
        fields=[
            FieldConfig(
                name="last_name",
                label="Apellido",
                type=ttk.Entry,
                required=True,
                converter=str,
                focus=True,
            ),
            FieldConfig(
                name="first_name",
                label="Nombre",
                type=ttk.Entry,
                required=True,
                converter=str,
            ),
        ],
    ),
    Section(
        title="Contacto",
        fields=[
            FieldConfig(
                name="phone1",
                label="Teléfono principal",
                type=ttk.Entry,
                required=True,
                converter=str,
            ),
            FieldConfig(
                name="phone2",
                label="Teléfono alternativo",
                type=ttk.Entry,
                converter=str,
            ),
            FieldConfig(
                name="phone3",
                label="Otro teléfono",
                type=ttk.Entry,
                converter=str,
            ),
        ],
    ),
    Section(
        title="Academico",
        fields=[
            FieldConfig(
                name="teacher",
                label="Profesor",
                type=ttk.Combobox,
                values=TEACHERS,
                required=True,
                converter=str,
            ),
            FieldConfig(
                name="book",
                label="Libro",
                type=ttk.Combobox,
                values=BOOKS,
                converter=str,
            ),
            FieldConfig(
                name="course",
                label="Curso",
                type=ttk.Combobox,
                values=COURSES,
                converter=str,
            ),
            FieldConfig(
                name="school",
                label="Escuela",
                type=ttk.Entry,
                converter=str,
            ),
            FieldConfig(
                name="school_year",
                label="Año Escolar",
                type=ttk.Combobox,
                values=YEAR,
                converter=str,
            ),
        ],
    ),
    Section(
        title="Administrativo",
        fields=[
            FieldConfig(
                name="monthly_fee",
                label="Cuota",
                type=ttk.Entry,
                required=True,
                numeric=True,
                converter=int,
            )
        ],
    ),
]


class AddStudentTab(BaseStudentFormTab):
    def __init__(self, parent: ttk.Notebook, main_service: ServiceContainer):
        super().__init__(
            parent=parent,
            form_title="Nuevo Estudiante",
            layout=FORM_LAYOUT,
            model_class=CreateStudentDTO,
        )

        self.s = main_service

        self.form_frame.pack(fill="both", padx=PAD_X, pady=PAD_Y)
        self.form_frame.columnconfigure(0, weight=1)

        # Define the specific UI for this tab
        self._create_fields_from_layout(0)
        self._create_action_button()
        self.bind_required_validation()

    def _create_action_button(self) -> None:
        """Create the 'Add' button."""
        self.image = ttk.PhotoImage(file=ICON_ADD)
        self.add_button = ttk.Button(
            self.form_frame,
            image=self.image,
            compound="left",
            text="Agregar Estudiante",
            command=self.add_student,
        )
        last_row = self.form_frame.grid_size()[1]
        self.add_button.grid(row=last_row, column=2, padx=PAD_X, pady=PAD_Y)

    def add_student(self):
        """Handles the student creation logic."""
        try:
            self.frame.config(cursor="watch")
            self.frame.update_idletasks()

            self.validate_form()

            data = self.mapper.to_model()

            self.add_button.config(text="Guardando...", state="disabled")

            result = self.actions.run(
                lambda: self.s.accounting.add_student(data),
                f"Se agrego al estudiante {data.first_name} {data.last_name}",
            )

            if result:
                self.state.clear_form()
                self.state.clear_form_styles()
                self.state.reset_comboboxes()
                next(iter(self.form_fields.values())).focus_set()

        except AppValidationError as e:
            show_toast(self.frame, str(e), "error")

        finally:
            self.add_button.config(text="Agregar Estudiante", state="normal")
            self.frame.config(cursor="")
            self.frame.update_idletasks()
