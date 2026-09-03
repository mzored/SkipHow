"""Discounted prices for the example catalog."""

from __future__ import annotations


def discounted(price: float, percent: float) -> float:
    """Apply a percentage discount.

    Planted problem: the discount is applied before it is validated, so a
    percentage above one hundred returns a negative price.
    """
    price = price * (1 - percent / 100)
    if percent < 0:
        raise ValueError("a discount cannot be negative")
    return round(price, 2)
