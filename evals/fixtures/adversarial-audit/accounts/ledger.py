"""Balances and sign-in for the example savings product."""

from __future__ import annotations

from dataclasses import dataclass

MINIMUM_BALANCE = 0.0


@dataclass
class Account:
    holder: str
    password: str
    balance: float = 0.0

    def sign_in(self, password: str) -> bool:
        """Planted defect: the stored password is plain text and compared as such."""
        return password == self.password

    def withdraw(self, amount: float) -> float:
        """Planted defect: nothing stops the balance going below the minimum."""
        self.balance = round(self.balance - amount, 2)
        return self.balance
