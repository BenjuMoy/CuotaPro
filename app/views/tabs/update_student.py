import ttkbootstrap as ttk
from ttkbootstrap.constants import DANGER, SUCCESS
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.tableview import Tableview

from app.models.exceptions import AppValidationError, ConflictError, NotFound
from app.models.models import Student
from app.services.application_service import ApplicationService
from app.utils.constantes import BOOKS, ICON_DELETE, ICON_EDIT, PAD_X, PAD_Y, TEACHERS
from app.views.base_tab import BaseFormTab
from app.views.helpers_gui import (
    create_label,
    enable_form_fields,
)
from app.views.toast import show_toast

FORM_LAYOUT = [
    {
        "section": "Identidad",
        "fields": [
            {
                "name": "id",
                "label": "ID",
                "type": "entry",
                "converter": int,
                "readonly": True,
            },
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


class UpdateStudentTab(BaseFormTab):
    def __init__(self, parent: ttk.Notebook, controller: ApplicationService) -> None:
        super().__init__(
            parent=parent,
            form_title="Datos del Estudiante",
            layout=FORM_LAYOUT,
            model_class=Student,
        )

        self.main_service = controller
        self.update_button: ttk.Button
        self.deactivate_button: ttk.Button

        self._setup_layout()
        self._create_student_list()
        self._create_fields_from_layout(1)
        self._create_action_buttons()
        self.bind_required_validation()
        self._set_state("search")

        self.main_service.subscribe(self.refresh_student_list)

    def _setup_layout(self):
        """Configure main layout structure."""
        self.main_frame = ttk.Frame(self.frame)
        self.main_frame.grid(sticky="nsew", padx=PAD_X, pady=PAD_Y)

        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=2)
        self.main_frame.rowconfigure(0, weight=1)

        self.form_frame.grid(row=0, column=1, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        # self.editing_label = ttk.Label(self.form_frame, text="asd")
        # self.editing_label.grid(row=1, column=1)

    def _create_student_list(self):
        """Create the student list table view."""
        list_frame = ttk.Labelframe(
            self.main_frame,
            text="Estudiantes Registrados",
            padding=10,
        )
        list_frame.grid(row=0, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        list_frame.configure(style="Bold.TLabelframe")

        create_label(
            list_frame, "Doble click en un estudiante para editarlo", 2, 0, False
        )
        # create_label(list_frame, "Seleccionar un estudiante de la lista:", 0, 0, False)

        columnas = ("ID", "Apellido", "Nombre", "Activo", "Profesor")
        students = self.main_service.get_all_students()
        rowdata = [self._student_to_row(est) for est in students]

        self.table = Tableview(
            list_frame,
            coldata=columnas,
            rowdata=rowdata,
            yscrollbar=True,
            autoalign=True,
        )
        self.table.grid(row=1, column=0, sticky="nsew", padx=PAD_X, pady=PAD_Y)
        self.table.view.bind("<Double-1>", self.on_double_click)

    def _create_action_buttons(self):
        """Create action buttons for the form."""
        button_frame = ttk.Frame(self.form_frame)
        button_frame.grid(row=len(FORM_LAYOUT), column=0, columnspan=3, pady=PAD_Y)

        self.image = ttk.PhotoImage(file=ICON_DELETE)
        self.deactivate_button = ttk.Button(
            button_frame,
            image=self.image,
            compound="left",
            text="Desactivar Estudiante",
            command=self.switch_sate,
            state="disabled",
            bootstyle=DANGER,
        )
        self.deactivate_button.pack(side="left", padx=PAD_X)

        self.image2 = ttk.PhotoImage(file=ICON_EDIT)
        self.update_button = ttk.Button(
            button_frame,
            image=self.image2,
            compound="left",
            text="Actualizar Estudiante",
            command=self.update_student,
            state="disabled",
        )
        self.update_button.pack(side="right", padx=PAD_X)

    def _set_state(self, state: str):
        """Set initial form state."""
        if state == "search":
            self.set_form_state(False)
        else:
            self.set_form_state(True)

    # --- Event Handlers --- #

    def on_double_click(self, event):
        """Handle double-click on student in table."""
        student_id = self._get_selected_id()
        if not student_id:
            return

        try:
            student = self.main_service.get_student_by_id(student_id)
            self._load_student_into_form(student)

        except NotFound as e:
            show_toast(self.frame, str(e), "error")

    def _get_selected_id(self) -> int | None:
        """Get the ID of the selected student from the table."""
        selected_rows = self.table.get_rows(selected=True)
        if not selected_rows:
            return None

        return int(selected_rows[0].values[0])

    def _load_student_into_form(self, student: Student):
        """Load student data into the form fields."""
        self._set_state("edit")
        self.populate_form(student)

        self.set_readonly_fields()

        enable_form_fields([self.update_button, self.deactivate_button])

        if not student.active:
            self.deactivate_button.config(
                text="Activar estudiante",
                bootstyle=SUCCESS,
                command=self.switch_sate,
            )
        else:
            self.deactivate_button.config(
                text="Desactivar estudiante", bootstyle=DANGER, command=self.switch_sate
            )

    def update_student(self):
        """Handle student update logic."""
        student_id_str = self.form_fields["id"].get().strip()
        if not student_id_str:
            return
        student_id = int(student_id_str)
        data = self.get_form_data()

        self.validate_form()

        try:
            _ = self._run_action(
                lambda: self.main_service.update_student(student_id, data),
                "Se actualizó el estudiante",
            )

            self._reset_form_state()
            self._set_state("search")
            self.table.selection_clear()

        except NotFound as e:
            show_toast(self.frame, str(e), "error")

        except AppValidationError as e:
            show_toast(self.frame, str(e), "error")

        except ConflictError as e:
            show_toast(self.frame, str(e), "error")

    def switch_sate(self):
        """Handle state switch"""
        result = Messagebox.yesno(
            f"¿Cambiar el estado de {self.form_fields['first_name'].get()} {self.form_fields['last_name'].get()}?",
            "Confirmar cambio",
        )

        if result != "Yes":
            return

        student_id = int(self.form_fields["id"].get())
        try:
            _ = self._run_action(
                lambda: self.main_service.switch_student_state(student_id),
                f"Se cambió el estado del estudiante {self.form_fields['first_name'].get()} {self.form_fields['last_name'].get()}",
            )

            self._reset_form_state()
            self._set_state("search")

        except NotFound:
            show_toast(self.frame, "Estudiante no encontrado", "error")

    def _reset_form_state(self):
        """Reset form after successful operation."""
        self.clear_form()
        self.set_form_state(False)
        enable_form_fields([self.update_button, self.deactivate_button], False)

    # --- Data Handling --- #

    def refresh_student_list(self):
        """Refresh the student table with updated data."""
        students = self.main_service.get_all_students()
        rowdata = [self._student_to_row(est) for est in students]

        self.table.delete_rows()
        self.table.insert_rows("end", rowdata)

    @staticmethod
    def _student_to_row(est: Student) -> tuple:
        """Convert student object to table row."""
        return (
            est.id,
            est.last_name,
            est.first_name,
            "✅ Activo" if est.active else "🚫 Inactivo",
            est.teacher,
        )
