import ttkbootstrap as ttk

from app.models.models import RefreshType
from app.services.application_service import ApplicationService
from app.utils.helpers import currency_format
from app.views.base_tab import BaseMetricsTab

CARDS = {
    "expected": "💰 Esperado",
    "collected": "✅ Cobrado",
    "debt": "⚠ Deuda",
}


class AnalyticsTab(BaseMetricsTab):
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        super().__init__(
            parent=parent,
            title="Analítica",
            cards=CARDS,
        )

        self.main_service = main_service

        self.create_kpi_cards()
        self.refresh()

        self.main_service.event.subscribe(RefreshType.STUDENTS, self.refresh)
        self.main_service.event.subscribe(RefreshType.MOVEMENTS, self.refresh)

    def refresh(self):
        metrics = self.main_service.get_kpi_metrics()

        self.cards["expected"].set(currency_format(metrics.expected_income))
        self.cards["collected"].set(currency_format(metrics.collected))
        self.cards["debt"].set(currency_format(metrics.total_debt))

        months, teachers, debt = self.main_service.get_graphic_metrics()
        self.draw_charts(months, teachers, debt)
