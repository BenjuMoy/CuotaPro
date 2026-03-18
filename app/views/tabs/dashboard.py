import ttkbootstrap as ttk

from app.models.models import RefreshType
from app.services.application_service import ApplicationService
from app.utils.constantes import TEACHERS
from app.views.base_tab import BaseMetricsTab

CARDS = {
    "student_card": "👨‍🎓 Estudiantes Activos",
    "teacher_card": "👩‍🏫 Profesores",
    "taken_card": "📊 Cobranza",
}

BUTTONS = {
    1: ("Agregar Estudiante", "success"),
    4: ("Registrar Pago", "primary"),
    2: ("Buscar Estudiante", "secondary"),
}


class DashboardTab(BaseMetricsTab):
    """Safe operational dashboard."""

    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        super().__init__(
            parent=parent, main_service=main_service, title="Inicio", cards=CARDS
        )
        self.service = main_service

        self.create_kpi_cards()
        self.build_buttons(BUTTONS)
        self.refresh()

        main_service.subscribe(RefreshType.STUDENTS, self.refresh)
        main_service.subscribe(RefreshType.MOVEMENTS, self.refresh)

    # -------------------------
    # DATA
    # -------------------------

    def refresh(self):
        metrics = self.service.get_kpi_metrics()

        self.cards["student_card"].set(str(metrics.active_students))
        self.cards["teacher_card"].set(str(len(TEACHERS)))

        rate = 0
        if metrics.expected_income > 0:
            rate = (metrics.collected / metrics.expected_income) * 100

        self.cards["taken_card"].set(f"{rate:.0f}%")
