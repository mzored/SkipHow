"""Historical monthly-report serialization."""


def monthly_row(row: tuple[str, str, float]) -> str:
    number, customer, amount = row
    return ",".join([number, customer, format(amount, ".2f")])
