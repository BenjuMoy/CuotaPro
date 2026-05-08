from dataclasses import dataclass
from typing import Literal

import ttkbootstrap as ttk

from ui.views.constants import FONT_BODY, FONT_TITLE, ICON_PATH
from ui.views.helpers_gui import center_window


@dataclass(frozen=True)
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: Literal["darkly", "yeti", "flatly"] = "yeti"


class TKRootFactory:
    def create_root(self, config: AppConfig | None = None) -> ttk.Window:
        """Creates and fully configures the root Tk window (theme, styles, fonts, icon)."""
        config = config or AppConfig()

        root = ttk.Window(
            themename=config.theme, title=config.window_title, iconphoto=str(ICON_PATH)
        )

        center_window(root)

        root.minsize(1280, 800)

        self.setup_styles(root)

        return root

    def setup_styles(self, root: ttk.Window) -> None:
        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=FONT_TITLE)
        style.configure("TCheckbutton", font=FONT_BODY)

        root.option_add("*TCombobox*Listbox.font", FONT_BODY)
