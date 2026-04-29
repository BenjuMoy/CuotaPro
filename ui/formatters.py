import locale


def currency_format(amount: int | str) -> str:
    # Set the locale to the user's default setting (usually the system locale)
    locale.setlocale(locale.LC_ALL, "")

    if isinstance(amount, str):
        amount = int(amount)

    # Format a number as currency
    currency_format = locale.currency(amount, grouping=True)
    return currency_format
    # return "${:,.2f}".format(num)
