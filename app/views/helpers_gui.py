import ttkbootstrap as ttk

from app.utils.constantes import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    FONT_BODY,
    FONT_HEADER,
    PAD_X,
    PAD_Y,
)


# --- widgets creation --- #
def create_label_frame(
    tab: ttk.Frame | ttk.Labelframe, text: str, expand: bool
) -> ttk.Labelframe:
    frame = ttk.Labelframe(tab, text=text, padding=10)
    if expand:
        frame.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)
    else:
        frame.pack(fill="x", padx=PAD_X, pady=PAD_Y)
    frame.configure(style="Bold.TLabelframe")

    return frame


def create_combobox(parent: ttk.Labelframe, row, column, values) -> ttk.Combobox:
    cb = ttk.Combobox(parent, values=values, state="readonly")
    cb.grid(row=row, column=column, sticky="ew", padx=PAD_X, pady=PAD_Y)
    return cb


def create_label(
    parent: ttk.Labelframe,
    text: str,
    row: int,
    column: int,
    required: bool = False,
    bold: bool = False,
) -> ttk.Label:
    label: ttk.Label = ttk.Label(parent, text=str(text), font=FONT_BODY)
    label.grid(row=row, column=column, sticky="w", padx=PAD_X, pady=PAD_Y)

    if required:
        label.config(text=f"{text} *")

    if bold:
        label.configure(font=(FONT_HEADER))

    return label


def create_entry(parent, row, column) -> ttk.Entry:
    entry = ttk.Entry(master=parent)
    entry.grid(row=row, column=column + 1, padx=PAD_X, pady=PAD_Y, sticky="ew")
    parent.columnconfigure(column + 1, weight=1)
    return entry


def create_label_entry(
    parent: ttk.Labelframe,
    text: str,
    row: int,
    column: int,
    focus: bool = False,
    required: bool = False,
) -> ttk.Entry:
    label = create_label(parent, text, row, column, required)
    entry = create_entry(parent, row, column)

    if focus:
        entry.focus_set()

    return entry


def create_label_combobox(
    parent: ttk.Labelframe,
    text: str,
    row: int,
    column: int,
    values: list[str],
    required: bool = False,
) -> ttk.Combobox:
    create_label(parent, text, row, column, required, False)

    cb = create_combobox(parent, row, column + 1, values)
    return cb


# --- Validators --- #
def get_str(entry: ttk.Entry) -> str:
    """Gets the raw string from an entry and strips whitespace."""
    return entry.get().strip()


def get_phones(entries: list[ttk.Entry]) -> list[str]:
    """Gets the raw phone number string."""
    return [e.get().strip() for e in entries if e.get().strip()]


# --- Style helpers --- #
def clear_inputs(entries: list[ttk.Entry | ttk.Combobox]) -> None:
    """Cleans input from list of entries."""
    for w in entries:
        if isinstance(w, ttk.Entry):
            w.delete(0, "end")
        elif isinstance(w, ttk.Combobox):
            w.set("")


def clear_style(entries: list[ttk.Entry | ttk.Combobox]):
    """Clears style from list of entries"""
    for entry in entries:
        entry.configure(style="")


def enable_form_fields(
    widgets: list[ttk.Entry | ttk.Combobox | ttk.Button], enabled: bool = True
):
    for w in widgets:
        if isinstance(w, ttk.Combobox):
            w.config(state="readonly" if enabled else "disabled")
        else:
            w.config(state="normal" if enabled else "disabled")


def enable_combobox(cb: ttk.Combobox) -> None:
    cb.config(state="readonly")


def mark_invalid(widget):
    style = "danger.TEntry"

    if isinstance(widget, ttk.Combobox):
        style = "danger.TCombobox"

    widget.configure(style=style)


def mark_valid(widget):
    widget.configure(style="")


def center_window(
    root: ttk.Window, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT
):
    """Recieves a window and centers it in the screen.

    Args:
        root (ttk.Window): the window.
        width (int): the width.
        height (int): The height.
    """
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    x = (screen_w // 2) - (width // 2)
    y = (screen_h // 2) - (height // 2)

    root.geometry(f"{width}x{height}+{x}+{y}")
