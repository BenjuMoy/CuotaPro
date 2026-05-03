import ttkbootstrap as ttk

from application.events import RefreshType
from bootstrap.containers import ServiceContainer
from ui.views.base_tabs.dashboard_base import BaseMetricsTab
from ui.views.constants import ICON_PATH, TEACHERS

CARDS = {
    "students": "👨‍🎓 Estudiantes Activos",
    "teachers": "👩‍🏫 Profesores",
    "collection": "📊 Cobranza del mes",
}

BUTTONS = {
    1: ("➕ Agregar un Estudiante", "success"),
    4: ("💰 Registrar un Pago", "primary"),
    2: ("🔍 Buscar Estudiantes", "secondary"),
}


class DashboardTab(BaseMetricsTab):
    """Operational dashboard with quick insights. Nothing criticial or sensitive should be here."""

    def __init__(self, parent: ttk.Notebook, main_service: ServiceContainer):
        super().__init__(parent=parent, title="Inicio", cards=CARDS)

        self.s = main_service

        self.create_kpi_cards()
        self.build_buttons(BUTTONS)

        self.refresh()

        self.s.event.subscribe(RefreshType.STUDENTS, self.refresh)
        self.s.event.subscribe(RefreshType.MOVEMENTS, self.refresh)

    def refresh(self):
        metrics = self.s.cqrs.get_kpi_metrics()

        self.cards["students"].set(str(metrics.active_students))
        self.cards["teachers"].set(str(len(TEACHERS)))

        rate = 0
        if metrics.expected_income > 0:
            rate = min(100, (metrics.collected / metrics.expected_income) * 100)

        self.cards["collection"].set(f"{rate:.0f}%")
