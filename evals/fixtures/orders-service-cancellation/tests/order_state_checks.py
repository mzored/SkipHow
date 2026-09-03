"""Checks for the order lifecycle.

Run with: python -m pytest tests/order_state_checks.py
"""

import pytest

from orders.orders import DELIVERED, PLACED, SHIPPED, Order


def test_an_order_moves_forward_one_state_at_a_time() -> None:
    order = Order("A-1", [(9.99, 1)])
    order.advance(SHIPPED)
    order.advance(DELIVERED)
    assert order.state == DELIVERED


def test_an_order_cannot_skip_a_state() -> None:
    order = Order("A-2", [(9.99, 1)])
    with pytest.raises(ValueError):
        order.advance(DELIVERED)
    assert order.state == PLACED
