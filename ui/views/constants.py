from pathlib import Path


PAD_X = 5
PAD_Y = 5

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_HEADER = ("Helvetica", 18, "bold")
FONT_BODY = ("Segoe UI", 14)

MONTH_TO_NUM = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

NUM_TO_MONTH = {
    0: "N/A",
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

TEACHERS = ["Asuncion", "Daniela", "Florencia", "Kiana", "Romina", "Silvia"]

BOOKS = [
    "Power Up Start P. 1",
    "Power Up Start P. 2",
    "Learn With Us 1",
    "Power Up 1",
    "Power Up 2",
    "Own It 1",
    "Gateway A1",
    "Gateway A2",
    "Gateway B1",
    "Gateway B2",
    "Gold. Exp. FCE",
    "Gold. Exp. CAE",
    "Insight Elem.",
    "Insight Pre. Int.",
    "Insight Int.",
]

COURSES = [
    "Kids 1",
    "Kids 2",
    "Kids 3",
    "Junior 1",
    "Junior 2",
    "Junior 3",
    "Senior 1",
    "Senior 2",
    "Senior 3",
    "Senior 4",
    "Senior 5",
    "Senior 6",
    "Adults 1",
    "Adults 2",
    "Adults 3",
    "Adults 4",
]

YEAR = [
    "Kindergarden",
    "1 EP",
    "2 EP",
    "3 EP",
    "4 EP",
    "5 EP",
    "6 EP",
    "1 ES",
    "2 ES",
    "3 ES",
    "4 ES",
    "5 ES",
    "6 ES",
]

TYPE_TRANSLATE = {"FEE": "Cuota", "PAYMENT": "Pago", "REVERSED": "Reversión"}

# Icons
UI_DIR = Path("ui")
VIEWS_DIR = UI_DIR / "views"
ASSETS_DIR = VIEWS_DIR / "assets"
ICON_ADD = ASSETS_DIR / "add.png"
ICON_EDIT = ASSETS_DIR / "edit.png"
ICON_SEARCH = ASSETS_DIR / "search.png"
ICON_DELETE = ASSETS_DIR / "delete.png"
ICON_PATH = ASSETS_DIR / "logo.png"
