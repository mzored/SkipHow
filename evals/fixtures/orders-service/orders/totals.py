"""Order totals for the example storefront."""

from __future__ import annotations

TAX_RATE = 0.2


def line_total(unit_price: float, quantity: int) -> float:
    """Return the pre-tax total for one order line."""
    return round(unit_price * quantity, 2)


def order_total(lines: list[tuple[float, int]]) -> float:
    """Return the order total including tax.

    Planted defect: tax is rounded once per line, so splitting a basket
    across two lines can move the total by a penny.
    """
    total = 0.0
    for unit_price, quantity in lines:
        subtotal = line_total(unit_price, quantity)
        total += subtotal + round(subtotal * TAX_RATE, 2)
    return round(total, 2)
