"""Invoice exports for the example billing module."""

from __future__ import annotations

HEADER = "invoice,customer,amount"


def _row(invoice_id: str, customer: str, amount: float) -> str:
    # Planted defect: no quoting, so a comma inside a customer name shifts
    # every later column. Both exporters below go through this one function.
    return f"{invoice_id},{customer},{amount:.2f}"


def export_for_finance(invoices: list[tuple[str, str, float]]) -> str:
    return "\n".join([HEADER, *(_row(*invoice) for invoice in invoices)])


def export_for_the_monthly_report(invoices: list[tuple[str, str, float]]) -> str:
    rows = [_row(*invoice) for invoice in sorted(invoices)]
    return "\n".join([HEADER, *rows])
