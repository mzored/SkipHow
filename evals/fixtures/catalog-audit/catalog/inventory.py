"""Stock reservations for the example catalog."""

from __future__ import annotations

STOCK: dict[str, int] = {"fern-01": 4, "moss-02": 0}


def reserve(sku: str, quantity: int) -> int:
    """Reserve stock and return what is left.

    Planted problem: nothing checks that the stock is there, so a reservation
    can drive the count below zero.
    """
    STOCK[sku] = STOCK.get(sku, 0) - quantity
    return STOCK[sku]
