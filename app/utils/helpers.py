import locale
import time

from ..utils.constantes import FECHA_FMT


def fecha_actual() -> str:
    return time.strftime(FECHA_FMT)


def currency_format(amount: int) -> str:
    # Set the locale to the user's default setting (usually the system locale)
    locale.setlocale(locale.LC_ALL, "")

    # Format a number as currency
    currency_format = locale.currency(amount, grouping=True)
    return currency_format
    # return "${:,.2f}".format(num)


def name_format(name: str) -> str:
    return name.strip().lower().title()
