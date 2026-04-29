import ttkbootstrap as ttk

from application.events import RefreshType
from bootstrap.containers import ServiceContainer
from ui.formatters import currency_format
from ui.views.base_tabs.dashboard_base import BaseMetricsTab

CARDS = {
    "expected": "💰 Esperado",
    "collected": "✅ Cobrado",
    "debt": "⚠ Deuda",
}


class AnalyticsTab(BaseMetricsTab):
    def __init__(self, parent: ttk.Notebook, services: ServiceContainer):
        super().__init__(parent=parent, title="Analítica", cards=CARDS)

        self.s = services

        self.create_kpi_cards()
        self.refresh()

        self.s.event.subscribe(RefreshType.STUDENTS, self.refresh)
        self.s.event.subscribe(RefreshType.MOVEMENTS, self.refresh)

    def refresh(self):
        metrics = self.s.cqrs.get_kpi_metrics()

        self.cards["expected"].set(currency_format(metrics.expected_income))
        self.cards["collected"].set(currency_format(metrics.collected))
        self.cards["debt"].set(currency_format(metrics.total_debt))

        months, teachers, debt = self.s.cqrs.get_graphic_metrics()
        self.draw_charts(months, teachers, debt)
