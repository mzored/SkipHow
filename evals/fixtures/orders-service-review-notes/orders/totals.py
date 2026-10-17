"""Order totals for the example storefront."""

from __future__ import annotations

TAX_RATE = 0.2


def line_total(unit_price: float, quantity: int) -> float:
    """Return the pre-tax total for one order line."""
    return round(unit_price * quantity, 2)


def line_tax(subtotal: float) -> float:
    """Return the tax on one line, rounded to the penny."""
    return round(subtotal * TAX_RATE, 2)


def order_total(lines: list[tuple[float, int]]) -> float:
    """Return the order total including tax, taxed once on the basket subtotal."""
    subtotal = sum(line_total(unit_price, quantity) for unit_price, quantity in lines)
    return round(subtotal + subtotal * TAX_RATE, 2)
