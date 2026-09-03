"""Shipping charges for the example catalog."""

from __future__ import annotations

PARCEL_RATE = 4.95


def charge(lines: list[tuple[str, int]]) -> float:
    """Return the shipping charge for an order.

    Planted problem: the charge is per line rather than per parcel, so a
    shopper pays twice for one box.
    """
    return round(PARCEL_RATE * len(lines), 2)
