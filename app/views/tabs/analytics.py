from collections import defaultdict
from tkinter import StringVar

import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.models.models import Movement, MovementType, Student
from app.services.application_service import ApplicationService
from app.utils.constantes import FONT_TITLE, NUM_TO_MONTH
from app.utils.helpers import currency_format


class AnalyticsTab:
    def __init__(self, parent: ttk.Notebook, main_service: ApplicationService):
        self.main_service = main_service
        self.frame = ttk.Frame(parent, padding=15)

        plt.style.use("seaborn-v0_8")

        self._build_ui()
        self.refresh()

        main_service.subscribe(self.refresh)

    # -------------------------
    # UI
    # -------------------------

    def _build_ui(self):
        title = ttk.Label(self.frame, text="Panel de Control", font=FONT_TITLE)
        title.pack(pady=10)

        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", pady=10)

        self.chart_frame = ttk.Frame(self.frame)
        self.chart_frame.pack(fill="both", expand=True)

        # KPI variables
        self.active_var = ttk.StringVar()
        self.expected_var = ttk.StringVar()
        self.collected_var = ttk.StringVar()
        self.debt_var = ttk.StringVar()
        self.rate_var = ttk.StringVar()

        # self._create_kpi("👨‍🎓 Estudiantes", self.active_var, 0)
        self._create_kpi("💰 Esperado", self.expected_var, 0)
        self._create_kpi("✅ Cobrado", self.collected_var, 1)
        self._create_kpi("⚠ Deuda", self.debt_var, 2)
        # self._create_kpi("📊 Cobranza", self.rate_var, 4)

    def _create_kpi(self, title: str, var: StringVar, col: int):
        card = ttk.Labelframe(self.kpi_frame, text=title, padding=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")

        label = ttk.Label(card, textvariable=var, font=("Helvetica", 16, "bold"))
        label.pack()

        self.kpi_frame.columnconfigure(col, weight=1)

    # -------------------------
    # DATA
    # -------------------------

    def refresh(self):
        metrics = self.main_service.get_kpi_metrics()

        if not metrics:
            return

        self.active_var.set(str(metrics.active_students))
        self.expected_var.set(currency_format(metrics.expected_income))
        self.collected_var.set(currency_format(metrics.collected))
        self.debt_var.set(currency_format(metrics.total_debt))

        rate = 0
        if metrics.expected_income > 0:
            rate = (metrics.collected / metrics.expected_income) * 100

        self.rate_var.set(f"{rate:.0f}%")

        students, movements = self.main_service.get_graphic_metrics()

        self._draw_charts(students, movements)

    # -------------------------
    # CHARTS
    # -------------------------

    def _draw_charts(self, students: list[Student], movements: list[Movement]):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig = plt.figure(figsize=(10, 6))
        gs = fig.add_gridspec(2, 2)

        income_ax = fig.add_subplot(gs[0, :])
        teacher_ax = fig.add_subplot(gs[1, 0])
        debt_ax = fig.add_subplot(gs[1, 1])

        # -------------------------
        # Income last 6 months
        # -------------------------

        income_by_month = defaultdict(int)

        for m in movements:
            if m.type == MovementType.PAYMENT:
                key = (m.year, NUM_TO_MONTH.get(m.month, "N/A"))
                income_by_month[key] += m.amount

        months_sorted = sorted(income_by_month.keys())[-6:]

        labels = [f"{m} / {y}" for y, m in months_sorted]
        values = [income_by_month[(y, m)] for y, m in months_sorted]

        income_ax.bar(labels, values)
        income_ax.set_title("Ingresos últimos 6 meses")
        income_ax.tick_params(axis="x", rotation=45)

        # -------------------------
        # Students per teacher
        # -------------------------

        teacher_count = defaultdict(int)

        for s in students:
            teacher_count[s.teacher] += 1

        sorted_teachers = sorted(
            teacher_count.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        teachers, counts = [], []

        for t, c in sorted_teachers:
            teachers.append(t)
            counts.append(c)

        teacher_ax.barh(teachers, counts)
        teacher_ax.set_title("Estudiantes por Profesor")

        # -------------------------
        # Payment status
        # -------------------------

        debt_buckets = {
            "Al día": 0,
            "1 mes": 0,
            "2 meses": 0,
            "3+ meses": 0,
        }

        balances = self.main_service.get_balances_for_students()
        for s in students:
            balance = balances[s.id]

            if balance >= 0:
                debt_buckets["Al día"] += 1
                continue

            months = abs(balance) // s.monthly_fee

            if months == 1:
                debt_buckets["1 mes"] += 1
            elif months == 2:
                debt_buckets["2 meses"] += 1
            else:
                debt_buckets["3+ meses"] += 1

        values = list(debt_buckets.values())
        labels = list(debt_buckets.keys())

        total = sum(values)

        if total == 0:
            debt_ax.text(
                0.5,
                0.5,
                "Sin datos",
                ha="center",
                va="center",
                fontsize=12,
            )
        else:
            debt_ax.pie(
                values,
                labels=labels,
                autopct="%1.0f%%",
            )

        debt_ax.set_title("Estado de Pagos")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        plt.close(fig)
