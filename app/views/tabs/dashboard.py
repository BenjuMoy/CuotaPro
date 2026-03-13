from tkinter import StringVar

import ttkbootstrap as ttk

from app.services.application_service import ApplicationService
from app.utils.constantes import FONT_BODY, FONT_HEADER, FONT_TITLE, TEACHERS

CARDS = {
    "student_card": "👨‍🎓 Estudiantes Activos",
    "teacher_card": "👩‍🏫 Profesores",
    "taken_card": "📊 Cobranza",
}

BUTTONS = {
    1: ("Agregar Estudiante", "success"),
    4: ("Registrar Pago", "prmary"),
    2: ("Buscar Estudiante", "secondary"),
}


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

        self.student_card: KpiCard
        self.teacher_card: KpiCard
        self.taken_card: KpiCard

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

        for i, (name, label) in enumerate(CARDS.items()):
            cls = KpiCard(self.kpi_frame, label)
            cls.grid(row=0, column=i, padx=20, pady=20, sticky="nsew")

            setattr(self, name, cls)

        for i in range(3):
            self.kpi_frame.columnconfigure(i, weight=1)

        # Quick actions
        actions = ttk.Labelframe(
            self.frame,
            text="Acciones rápidas",
            padding=15,
        )
        actions.pack(fill="x", padx=20, pady=20)

        for idx, (label, style) in BUTTONS.items():
            ttk.Button(
                actions,
                text=label,
                bootstyle=style,
                command=lambda: self.parent.select(idx),
            ).pack(side="left", padx=20, pady=20, expand=True, fill="both")

    # -------------------------
    # DATA
    # -------------------------

    def refresh(self):

        metrics = self.service.get_kpi_metrics()

        self.student_card.set(str(metrics.active_students))
        self.teacher_card.set(str(len(TEACHERS)))

        rate = 0
        if metrics.expected_income > 0:
            rate = (metrics.collected / metrics.expected_income) * 100

        self.taken_card.set(f"{rate:.0f}%")
