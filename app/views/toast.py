# views/toast.py
import ttkbootstrap as ttk

from app.utils.constantes import FONT_BODY


class Toast:
    def __init__(
        self,
        parent: ttk.Frame | ttk.Window,
        message: str,
        toast_type: str,
        duration: int = 3000,
    ):
        self.parent = parent
        self.message = message
        self.duration = duration

        # Create a new toplevel window
        self.toast = ttk.Toplevel(master=parent)
        self.toast.overrideredirect(True)  # Remove window decorations
        self.toast.config(bg="#3a3a3a")

        # Position the toast at the bottom-right of the parent
        self.toast.geometry(
            f"+{parent.winfo_x() + parent.winfo_width() - 250}+{parent.winfo_y() + parent.winfo_height() - 100}"
        )

        if toast_type == "success":
            bg = "#2e7d32"
        elif toast_type == "error":
            bg = "#d32f2f"
        else:
            bg = "#ed6c02"

        # Add a label
        label = ttk.Label(
            self.toast,
            text=message,
            padding=10,
            background=bg,
            foreground="white",
            font=FONT_BODY,
        )
        label.pack()

        # Schedule the toast to close itself
        self.toast.after(self.duration, self.close)

    def close(self):
        self.toast.destroy()


# Helper function
def show_toast(
    parent: ttk.Frame | ttk.Window,
    message: str,
    toast_type: str,
    duration: int = 3000,
):
    Toast(parent, message, toast_type, duration)
