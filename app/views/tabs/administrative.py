import ttkbootstrap as ttk

from app.services.application_service import ApplicationService
from app.views.tabs.admin.fee_application_panel import FeeApplicationPanel
from app.views.tabs.admin.fee_increase_panel import FeeIncreasePanel
from app.views.tabs.admin.movement_table_panel import MovementTablePanel


class AdministrativeTab:
    def __init__(self, parent: ttk.Notebook, controller: ApplicationService):
        self.main_service = controller
        frame = ttk.Frame(parent)
        self.frame = frame

        self.fee_aplication = FeeApplicationPanel(frame, controller)

        self.fee_increase = FeeIncreasePanel(frame, controller)

        self.movements = MovementTablePanel(frame, controller)

        self.main_service.subscribe(self.movements.refresh_table)
