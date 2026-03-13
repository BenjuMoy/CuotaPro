from tkinter import StringVar

import ttkbootstrap as ttk

from app.services.application_service import ApplicationService
from app.utils.constantes import FONT_BODY, FONT_HEADER, FONT_TITLE, TEACHERS


class KpiCard(ttk.Labelframe):
    def __init__(self, parent: ttk.Frame, title: str):
        super().__init__(parent, text=title, padding=15)

        self.var = StringVar()

        self.label = ttk.Label(
            self,
            textvariable=self.var,
            font=FONT_HEADER,
        )

        self.label.pack()

    def set(self, value: str):
        self.var.set(value)


class DashboardTab:
    """Safe operational dashboard."""

    def __init__(self, parent: ttk.Notebook, service: ApplicationService):
        self.parent = parent
        self.service = service
        self.frame = ttk.Frame(parent, padding=20)

        self._build_ui()
        self.refresh()

        service.subscribe(self.refresh)

    # -------------------------
    # UI
    # -------------------------

    def _build_ui(self):

        title = ttk.Label(
            self.frame,
            text="Panel de Control",
            font=FONT_TITLE,
        )
        title.pack(padx=20, pady=20)

        # KPIs
        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", padx=20, pady=20)

        self.students_card = KpiCard(self.kpi_frame, "👨‍🎓 Estudiantes Activos")
        self.students_card.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.teachers_card = KpiCard(self.kpi_frame, "👩‍🏫 Profesores")
        self.teachers_card.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # self.recent_card = KpiCard(self.kpi_frame, "📅 Movimientos Hoy")
        # self.recent_card.grid(row=0, column=2, padx=10, sticky="nsew")

        self.taken_card = KpiCard(self.kpi_frame, "📊 Cobranza")
        self.taken_card.grid(row=0, column=2, padx=20, pady=20, sticky="nsew")

        for i in range(3):
            self.kpi_frame.columnconfigure(i, weight=1)

        # Quick actions
        actions = ttk.Labelframe(
            self.frame,
            text="Acciones rápidas",
            padding=15,
        )
        actions.pack(fill="x", padx=20, pady=20)

        ttk.Button(
            actions,
            text="Agregar Estudiante",
            bootstyle="success",
            command=lambda: self.parent.select(1),
        ).pack(side="left", padx=20, pady=20, expand=True, fill="both")

        ttk.Button(
            actions,
            text="Registrar Pago",
            bootstyle="primary",
            command=lambda: self.parent.select(4),
        ).pack(side="left", padx=20, pady=20, expand=True, fill="both")

        ttk.Button(
            actions,
            text="Buscar Estudiante",
            bootstyle="secondary",
            command=lambda: self.parent.select(2),
        ).pack(side="left", padx=20, pady=20, expand=True, fill="both")

    # -------------------------
    # DATA
    # -------------------------

    def refresh(self):

        metrics = self.service.get_kpi_metrics()

        self.students_card.set(str(metrics.active_students))
        self.teachers_card.set(str(len(TEACHERS)))

        rate = 0
        if metrics.expected_income > 0:
            rate = (metrics.collected / metrics.expected_income) * 100

        self.taken_card.set(f"{rate:.0f}%")
