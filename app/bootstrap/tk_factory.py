import ttkbootstrap as ttk

from app.utils.constantes import ICON_PATH


class TkAppFactory:
    @staticmethod
    def create_root(theme: str, title: str) -> ttk.Window:
        root = ttk.Window(themename=theme)
        root.title(title)

        # Better geometry: 1280x800 centered
        width = 1366
        height = 768
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)

        root.geometry(f"{width}x{height}+{x}+{y}")
        root.minsize(1280, 800)

        icon = ttk.PhotoImage(file=ICON_PATH)
        root.iconphoto(True, icon)

        return root
