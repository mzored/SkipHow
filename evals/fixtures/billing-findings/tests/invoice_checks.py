"""Checks for the example billing module.

Run with: python -m pytest tests/invoice_checks.py

The module is deliberately not named test_*.py, so that a bare pytest run in
the SkipHow repository never collects this fixture.
"""

from billing.invoices import invoice_total, line_amount


def test_single_line_invoice_totals() -> None:
    assert invoice_total([(19.99, 1)]) == line_amount(19.99, 1)


def test_invoice_total_matches_the_amounts_the_customer_sees() -> None:
    lines = [(19.99, 3), (9.99, 3), (4.99, 3)]
    assert invoice_total(lines) == round(sum(line_amount(*line) for line in lines), 2)
