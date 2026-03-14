import ttkbootstrap as ttk

from app.utils.constantes import FONT_HEADER


class KpiCard(ttk.Labelframe):
    def __init__(self, parent: ttk.Frame, title: str):
        super().__init__(parent, text=title, padding=15)

        self.var = ttk.StringVar()

        self.label = ttk.Label(
            self,
            textvariable=self.var,
            font=FONT_HEADER,
        )

        self.label.pack()

    def set(self, value: str):
        self.var.set(value)
