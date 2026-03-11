# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
from pathlib import Path

APP_VERSION = "1.3.1"

LOGS_DIR = Path("logs/")
LOGS_PATH = Path("logs/app.log")


ABOUT_TEXT = "Desarrollado por Benjamin Moyano\nmoyano [dot] ben [at] gmail [dot] com"


# Database-related constants
DATABASE_DIR = "data/"
DATABASE_PATH = "data/student_management.db"
DATABASE_BACKUP_DIR = "data/backup/"
DATABASE_EXPORT_DIR = "data/exports/"

# Icons
ICON_ADD = "app/views/assets/add.png"
ICON_EDIT = "app/views/assets/edit.png"
ICON_SEARCH = "app/views/assets/search.png"
ICON_DELETE = "app/views/assets/delete.png"
ICON_PATH = "app/views/assets/logo.png"


FECHA_FMT = "%d-%m-%Y"
FECHA_HOY_AHORA_FMT = "%Y/%m/%d %H:%M:%S"

ID_PREDETERMINADO = 0


CAMPO_ID = "id"
CAMPO_ACTIVO = "activo"
CAMPO_APELLIDO = "apellido"
CAMPO_NOMBRE = "nombre"
CAMPO_PROFESOR = "profesor"
CAMPO_TELEFONOS = "telefonos"
CAMPO_BALANCE = "balance"
CAMPO_LIBRO = "libro"
CAMPO_CURSO = "curso"
CAMPO_ESCUELA = "escuela"
CAMPO_ANIO = "anio"
CAMPO_CUOTA = "cuota"
CAMPO_ULTIMO_MES_PAGADO = "ultimo mes pagado"

CAMPO_FECHA_PAGADA = "fecha_pagada"
CAMPO_MONTO = "monto"
CAMPO_MES_PAGADO = "mes_pagado"

PAD_X = 5
PAD_Y = 5

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

COURSES = []

MIN_YEAR = 2020
MAX_YEAR = 2100
CURRENCY = "ARS"

TYPE_TRANSLATE = {"FEE": "Cuota", "PAYMENT": "Pago", "REVERSED": "Reversión"}

DEFAULT_WIDTH = 1366
DEFAULT_HEIGHT = 768
