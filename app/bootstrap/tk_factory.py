import ttkbootstrap as ttk

from app.utils.constantes import (
    FONT_BODY,
    FONT_HEADER,
    FONT_TITLE,
    ICON_PATH,
)
from app.views.helpers_gui import center_window


class TkAppFactory:
    """Sets up the man window.

    Returns:
        Window: main window
    """

    @staticmethod
    def create_root(theme: str, title: str) -> ttk.Window:
        root = ttk.Window(themename=theme)
        root.title(title)

        center_window(root)

        root.minsize(1280, 800)

        root._icon = ttk.PhotoImage(file=ICON_PATH)
        root.iconphoto(True, root._icon)

        # Set up styles
        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=(FONT_TITLE))

        root.option_add("*TCombobox*Listbox.font", FONT_BODY)

        return root
