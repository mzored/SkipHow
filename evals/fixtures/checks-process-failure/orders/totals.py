"""Healthy order totals used to isolate a project-check process failure."""

from __future__ import annotations

TAX_RATE = 0.2


def line_total(unit_price: float, quantity: int) -> float:
    """Return the pre-tax total for one order line."""
    return round(unit_price * quantity, 2)


def order_total(lines: list[tuple[float, int]]) -> float:
    """Return the order total including tax, rounded once per order."""
    subtotal = sum(unit_price * quantity for unit_price, quantity in lines)
    return round(subtotal + round(subtotal * TAX_RATE, 2), 2)
