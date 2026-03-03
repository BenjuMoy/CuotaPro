from collections import defaultdict
from datetime import datetime

import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# from ttkbootstrap.constants import *
from app.utils.helpers import currency_format


class DashboardTab:
    def __init__(self, parent, controller):
        self.controller = controller
        self.frame = ttk.Frame(parent, padding=15)

        self._build_ui()
        self.refresh()

        controller.subscribe(self.refresh)

    # -------------------------
    # UI LAYOUT
    # -------------------------

    def _build_ui(self):
        title = ttk.Label(
            self.frame,
            text="Panel de Control",
            font=("Helvetica", 22, "bold"),
        )
        title.pack(pady=10)

        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", pady=10)

        self.chart_frame = ttk.Frame(self.frame)
        self.chart_frame.pack(fill="both", expand=True)

        self.active_var = ttk.StringVar()
        self.expected_var = ttk.StringVar()
        self.collected_var = ttk.StringVar()
        self.debt_var = ttk.StringVar()

        self._create_kpi("Estudiantes Activos", self.active_var, 0)
        self._create_kpi("Ingreso Esperado", self.expected_var, 1)
        self._create_kpi("Cobrado Mes", self.collected_var, 2)
        self._create_kpi("Deuda Total", self.debt_var, 3)

    def _create_kpi(self, title, var, col):
        card = ttk.Labelframe(self.kpi_frame, text=title, padding=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")

        label = ttk.Label(card, textvariable=var, font=("Helvetica", 16, "bold"))
        label.pack()

        self.kpi_frame.columnconfigure(col, weight=1)

    # -------------------------
    # DATA + CHARTS
    # -------------------------

    def refresh(self):
        now = datetime.now()

        students = self.controller.get_all_active_students()
        movements = self.controller.get_effective_payments()

        active_count = len(students)
        expected = sum(s.monthly_fee for s in students)

        collected = sum(
            m.amount for m in movements if m.month == now.month and m.year == now.year
        )

        debt_total = sum(self.controller.get_balance_by_id(s.id) for s in students)

        self.active_var.set(str(active_count))
        self.expected_var.set(f"{currency_format(expected)}")
        self.collected_var.set(f"{currency_format(collected)}")
        self.debt_var.set(f"{currency_format(debt_total)}")

        # self._draw_charts(students, movements)

    # -------------------------
    # CHARTS
    # -------------------------

    def _draw_charts(self, students, movements):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        # ---- Income per month (last 6 months)
        income_by_month = defaultdict(int)

        for m in movements:
            key = f"{m.month}/{m.year}"
            income_by_month[key] += m.amount

        months = list(income_by_month.keys())[-6:]
        values = [income_by_month[m] for m in months]

        axes[0].bar(months, values)
        axes[0].set_title("Ingresos por Mes")
        axes[0].tick_params(axis="x", rotation=45)

        # ---- Students per teacher
        teacher_count = defaultdict(int)
        for s in students:
            teacher_count[s.teacher] += 1

        teachers = list(teacher_count.keys())  # Replace with TEACHERS constant
        counts = list(teacher_count.values())

        axes[1].bar(teachers, counts)
        axes[1].set_title("Estudiantes por Profesor")
        axes[1].tick_params(axis="x", rotation=45)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
