import ttkbootstrap as ttk

from app.utils.constantes import ABOUT_TEXT, APP_VERSION, FONT_HEADER
from app.views.helpers_gui import center_window

DIALOG_SIZES = {
    "about": (100, 100),
}


def show_about(root: ttk.Window) -> None:
    """Sets up the about window.

    Args:
        root (ttk.Window): Parent window.
    """
    dialog = ttk.Toplevel(root)
    dialog.title("Sobre la Aplicación")
    dialog.geometry(f"{DIALOG_SIZES['about'][0]}x{DIALOG_SIZES['about'][1]}")
    dialog.transient(root)
    dialog.grab_set()

    ttk.Label(
        dialog,
        text="Gestor de Estudiantes",
        font=(FONT_HEADER),
    ).pack(pady=10)

    ttk.Label(
        dialog,
        text=f"Versión {APP_VERSION}",
        font=("Helvetica", 12),
    ).pack(pady=5)

    ttk.Label(
        dialog,
        text="""Sistema de gestión para academias.\n\n
        Permite controlar estudiantes, pagos,\n
        deudas y salarios docentes.""",
        justify="center",
    ).pack(pady=10)

    ttk.Label(
        dialog,
        text=ABOUT_TEXT,
        font=("Helvetica", 10),
    ).pack(pady=10)

    ttk.Button(dialog, text="Cerrar", command=dialog.destroy).pack(pady=15)

    center_window(dialog)
