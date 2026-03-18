import ttkbootstrap as ttk

from app.services.application_service import ApplicationService
from app.views.tabs.admin.fee_application_panel import FeeApplicationPanel
from app.views.tabs.admin.fee_increase_panel import FeeIncreasePanel
from app.views.tabs.admin.movement_table_panel import MovementTablePanel


class AdministrativeTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service = main_service
        frame = ttk.Frame(parent)
        self.frame = frame

        self.fee_application = FeeApplicationPanel(frame, main_service)

        self.fee_increase = FeeIncreasePanel(frame, main_service)

        self.movements = MovementTablePanel(frame, main_service)
