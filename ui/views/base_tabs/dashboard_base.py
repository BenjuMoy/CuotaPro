import matplotlib.pyplot as plt
import ttkbootstrap as ttk
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ui.views.constants import FONT_TITLE, NUM_TO_MONTH
from ui.views.widgets.kpi_card import KpiCard


class BaseMetricsTab:
    def __init__(
        self,
        parent: ttk.Notebook,
        title: str,
        cards: dict[str, str],
    ):
        self.parent = parent
        self.frame = ttk.Frame(parent, padding=25)

        self.title = title
        self.kpi_config = cards

        self.cards: dict[str, KpiCard] = {}

        self.chart_style = "seaborn-v0_8"
        self.chart_frame: ttk.Frame | None = None

        self.canvas: FigureCanvasTkAgg | None = None
        self.fig = None

    # -------------------------
    # CARDS
    # -------------------------

    def create_kpi_cards(self):
        ttk.Label(
            self.frame,
            text=self.title,
            font=FONT_TITLE,
        ).pack(pady=15)

        self.kpi_frame = ttk.Frame(self.frame)
        self.kpi_frame.pack(fill="x", pady=10)

        for i, (name, label) in enumerate(self.kpi_config.items()):
            card = KpiCard(self.kpi_frame, label)
            card.grid(row=0, column=i, padx=15, pady=10, sticky="nsew")

            self.kpi_frame.columnconfigure(i, weight=1)
            self.cards[name] = card

    # -------------------------
    # BUTTONS
    # -------------------------

    def build_buttons(self, buttons: dict[int, tuple[str, str]]):
        actions = ttk.Labelframe(
            self.frame,
            text="Acciones rápidas",
            padding=15,
        )
        actions.pack(fill="x", pady=15)

        for idx, (label, style) in buttons.items():
            ttk.Button(
                actions,
                text=label,
                bootstyle=style,
                command=lambda tab_index=idx: self.parent.select(tab_index),
            ).pack(side="left", padx=10, pady=10, expand=True, fill="x")

    # -------------------------
    # CHARTS
    # -------------------------

    def draw_charts(
        self,
        income_by_month: dict[tuple[int, int], int],
        teacher_count: dict[str, int],
        debt_bucket: dict[str, int],
    ):
        if self.chart_frame is None:
            self.chart_frame = ttk.Frame(self.frame)
            self.chart_frame.pack(fill="both", expand=True)

        plt.style.use(self.chart_style)

        if self.fig is None:
            self.fig = plt.figure(figsize=(10, 6))
            self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.fig.clear()
        gs = self.fig.add_gridspec(2, 2)

        self._draw_income_chart(self.fig.add_subplot(gs[0, :]), income_by_month)
        self._draw_teacher_chart(self.fig.add_subplot(gs[1, 0]), teacher_count)
        self._draw_debt_chart(self.fig.add_subplot(gs[1, 1]), debt_bucket)

        self.fig.tight_layout()
        self.canvas.draw()

    # -------------------------
    # CHARTS IMPLEMENTATION
    # -------------------------

    def _draw_income_chart(self, ax: Axes, data: dict[tuple[int, int], int]):
        items = list(data.items())
        labels = [f"{NUM_TO_MONTH[m]} / {y}" for (m, y), _ in items]
        values = [v for _, v in items]

        x = range(len(labels))

        ax.bar(x, values)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)

        ax.set_title("Ingresos últimos 6 meses")
        ax.tick_params(axis="x", rotation=45)

    def _draw_teacher_chart(self, ax: Axes, data: dict):
        names = list(data.keys())
        values = [int(v) for v in data.values()]

        ax.barh(names, values)
        ax.set_title("Estudiantes por Profesor")

    def _draw_debt_chart(self, ax: Axes, data: dict):
        values = list(data.values())
        labels = list(data.keys())

        total = sum(values)

        if total == 0:
            ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
            return

        colors = ["green", "gold", "orange", "red"][: len(values)]

        ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
        )

        ax.set_title("Estado de Pagos")
