import ttkbootstrap as ttk

from app.utils.constantes import DEFAULT_HEIGHT, DEFAULT_WIDTH, ICON_PATH


def _center_window(root, width, height):
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)

    root.geometry(f"{width}x{height}+{x}+{y}")


class TkAppFactory:
    @staticmethod
    def create_root(theme: str, title: str) -> ttk.Window:
        root = ttk.Window(themename=theme)
        root.title(title)

        width = DEFAULT_WIDTH
        height = DEFAULT_HEIGHT

        _center_window(root, width, height)

        root.minsize(1280, 800)

        root._icon = ttk.PhotoImage(file=ICON_PATH)
        root.iconphoto(True, root._icon)

        return root
