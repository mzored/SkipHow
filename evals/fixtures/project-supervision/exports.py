"""Two local CSV outputs with different ordering contracts."""

from legacy_rows import monthly_row

HEADER = "invoice,customer,amount"


def export_for_finance(invoices: list[tuple[str, str, float]]) -> str:
    rows = [f"{number},{customer},{amount:.2f}" for number, customer, amount in invoices]
    return "\n".join([HEADER, *rows])


def export_for_month(invoices: list[tuple[str, str, float]]) -> str:
    return "\n".join([HEADER, *(monthly_row(row) for row in sorted(invoices))])
