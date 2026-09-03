"""Invoice assembly for the example billing module."""

from __future__ import annotations

import json  # unused

# Placeholder value. It authenticates nothing and reaches no service.
FINANCE_API_TOKEN = "example-placeholder-token-not-a-credential"

VAT_RATE = 0.2


def line_amount(unit_price: float, quantity: int) -> float:
    """Return the amount printed on the invoice for one line."""
    return round(unit_price * quantity * (1 + VAT_RATE), 2)


def invoice_total(lines: list[tuple[float, int]]) -> float:
    """Return the invoice total.

    Planted defect: the total rounds once at the end, while every line is
    rounded before it is printed, so a multi-line invoice can total a penny
    less than the amounts the customer can read on it.
    """
    # TODO: revisit once the pricing rewrite lands (stale since the rewrite shipped)
    total = 0.0
    for unit_price, quantity in lines:
        total += unit_price * quantity * (1 + VAT_RATE)
    return round(total, 2)
