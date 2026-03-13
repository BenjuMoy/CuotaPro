import ttkbootstrap as ttk

from app.models.exceptions import AppValidationError
from app.models.models import Student
from app.services.application_service import ApplicationService
from app.utils.constantes import BOOKS, ICON_ADD, PAD_X, PAD_Y, TEACHERS
from app.views.base_tab import BaseStudentFormTab
from app.views.toast import show_toast

FORM_LAYOUT = [
    {
        "section": "Identidad",
        "fields": [
            {
                "name": "last_name",
                "label": "Apellido",
                "type": "entry",
                "required": True,
                "converter": str,
                "focus": True,
            },
            {
                "name": "first_name",
                "label": "Nombre",
                "type": "entry",
                "required": True,
                "converter": str,
            },
        ],
    },
    {
        "section": "Contacto",
        "fields": [
            {
                "name": "phone1",
                "label": "Teléfono principal",
                "type": "entry",
                "required": True,
                "converter": str,
            },
            {
                "name": "phone2",
                "label": "Teléfono alternativo",
                "type": "entry",
                "converter": str,
            },
            {
                "name": "phone3",
                "label": "Otro teléfono",
                "type": "entry",
                "converter": str,
            },
        ],
    },
    {
        "section": "Academico",
        "fields": [
            {
                "name": "teacher",
                "label": "Profesor",
                "type": "combobox",
                "values": TEACHERS,
                "required": True,
                "converter": str,
            },
            {
                "name": "book",
                "label": "Libro",
                "type": "combobox",
                "values": BOOKS,
                "converter": str,
            },
            {
                "name": "course",
                "label": "Curso",
                "type": "entry",
                "converter": str,
            },
            {
                "name": "school",
                "label": "Escuela",
                "type": "entry",
                "converter": str,
            },
            {
                "name": "year",
                "label": "Año",
                "type": "entry",
                "converter": str,
            },
        ],
    },
    {
        "section": "Administrativo",
        "fields": [
            {
                "name": "monthly_fee",
                "label": "Cuota",
                "type": "entry",
                "required": True,
                "numeric": True,
                "converter": int,
            }
        ],
    },
]


class AddStudentTab(BaseStudentFormTab):
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        super().__init__(
            parent=parent,
            form_title="Nuevo Estudiante",
            layout=FORM_LAYOUT,
            model_class=Student,
        )

        self.main_service = main_service
        self.main_frame.pack(fill="both")

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
        self.add_button.grid(row=len(FORM_LAYOUT), column=2, padx=PAD_X, pady=PAD_Y)

    def add_student(self):
        """Handles the student creation logic."""
        try:
            self.validate_form()

            data = self.get_form_data()

            self.add_button.config(text="Guardando...", state="disabled")

            result = self._run_action(
                lambda: self.main_service.add_student(data),
                f"Se agrego al estudiante {data['first_name']} {data['last_name']}",
            )

            if result:
                self.clear_form()
                self.clear_form_styles()
                self.form_fields["teacher"].set("")
                self.form_fields["book"].set("")
                self.form_fields["last_name"].focus_set()

        except AppValidationError as e:
            show_toast(self.frame, str(e), "error")

        finally:
            self.add_button.config(text="Agregar Estudiante", state="normal")
