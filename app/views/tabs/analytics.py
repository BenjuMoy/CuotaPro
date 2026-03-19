import ttkbootstrap as ttk

from app.models.models import RefreshType
from app.services.application_service import ApplicationService
from app.utils.helpers import currency_format
from app.views.base_tab import BaseMetricsTab

CARDS = {
    "expected_card": "💰 Esperado",
    "collected_card": "✅ Cobrado",
    "debt_card": "⚠ Deuda",
}


class AnalyticsTab(BaseMetricsTab):
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        super().__init__(
            parent=parent,
            title="Analitica",
            cards=CARDS,
        )
        self.main_service = main_service

        self.create_kpi_cards()
        self.draw_charts(*self.main_service.get_graphic_metrics())
        self.refresh()

        self.main_service.subscribe(RefreshType.STUDENTS, self.refresh)
        self.main_service.subscribe(RefreshType.MOVEMENTS, self.refresh)

    # -------------------------
    # DATA
    # -------------------------

    def refresh(self):
        metrics = self.main_service.get_kpi_metrics()

        if not metrics:
            return

        self.cards["expected_card"].set(currency_format(metrics.expected_income))
        self.cards["collected_card"].set(currency_format(metrics.collected))
        self.cards["debt_card"].set(currency_format(metrics.total_debt))
