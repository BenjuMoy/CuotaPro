import ttkbootstrap as ttk

from bootstrap.containers import ServiceContainer
from ui.views.tabs.admin.fee_application_panel import FeeApplicationPanel
from ui.views.tabs.admin.fee_increase_panel import FeeIncreasePanel
from ui.views.tabs.admin.movement_table_panel import MovementTablePanel


class AdministrativeTab:
    def __init__(self, parent: ttk.Notebook, main_service: ServiceContainer):
        self.main_service = main_service
        frame = ttk.Frame(parent)
        self.frame = frame

        self.fee_application = FeeApplicationPanel(frame, main_service)

        self.fee_increase = FeeIncreasePanel(frame, main_service)

        self.movements = MovementTablePanel(frame, main_service)
