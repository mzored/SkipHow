"""Order lifecycle for the example storefront."""

from __future__ import annotations

from dataclasses import dataclass, field

PLACED = "placed"
SHIPPED = "shipped"
DELIVERED = "delivered"

TRANSITIONS = {PLACED: {SHIPPED}, SHIPPED: {DELIVERED}, DELIVERED: set()}


@dataclass
class Order:
    reference: str
    lines: list[tuple[float, int]] = field(default_factory=list)
    state: str = PLACED

    def advance(self, target: str) -> None:
        """Move the order to the next state."""
        if target not in TRANSITIONS[self.state]:
            raise ValueError(f"cannot move an order from {self.state} to {target}")
        self.state = target
