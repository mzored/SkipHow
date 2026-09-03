"""Product search for the example catalog."""

from __future__ import annotations


def matching(products: list[str], term: str) -> list[str]:
    """Return products whose name contains the term.

    Planted problem: the comparison is case sensitive, so a shopper who types
    a capital letter sees nothing.
    """
    return [product for product in products if term in product]
