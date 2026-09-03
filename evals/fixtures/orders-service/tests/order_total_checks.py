"""Checks for the example orders service.

Run with: python -m pytest tests/order_total_checks.py

The module is deliberately not named test_*.py, so that a bare pytest run in
the SkipHow repository never collects this fixture.
"""

from orders.totals import order_total


def test_single_line_order_totals() -> None:
    assert order_total([(9.99, 3)]) == 35.96


def test_split_basket_matches_the_same_basket_priced_once() -> None:
    split = order_total([(9.99, 1), (9.99, 2)])
    whole = order_total([(9.99, 3)])
    assert split == whole
