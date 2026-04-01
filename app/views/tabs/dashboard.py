import ttkbootstrap as ttk

from app.models.models import RefreshType
from app.services.application_service import ApplicationService
from app.utils.constantes import TEACHERS
from app.views.base_tab import BaseMetricsTab

CARDS = {
    "students": "👨‍🎓 Estudiantes Activos",
    "teachers": "👩‍🏫 Profesores",
    "collection": "📊 Cobranza",
}

BUTTONS = {
    1: ("Agregar Estudiante", "success"),
    4: ("Registrar Pago", "primary"),
    2: ("Buscar Estudiante", "secondary"),
}


class DashboardTab(BaseMetricsTab):
    """Operational dashboard with quick insights."""

    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        super().__init__(parent=parent, title="Inicio", cards=CARDS)

        self.main_service = main_service

        self.create_kpi_cards()
        self.build_buttons(BUTTONS)

        self.refresh()

        self.main_service.event.subscribe(RefreshType.STUDENTS, self.refresh)
        self.main_service.event.subscribe(RefreshType.MOVEMENTS, self.refresh)

    def refresh(self):
        metrics = self.main_service.get_kpi_metrics()

        self.cards["students"].set(str(metrics.active_students))
        self.cards["teachers"].set(str(len(TEACHERS)))

        rate = 0
        if metrics.expected_income > 0:
            rate = (metrics.collected / metrics.expected_income) * 100

        self.cards["collection"].set(f"{rate:.0f}%")
