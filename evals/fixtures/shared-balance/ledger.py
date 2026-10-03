"""Synthetic account operations, using integer units and no external systems."""


def _debit(balances: dict[str, int], account: str, amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    balances[account] -= amount


def transfer(balances: dict[str, int], source: str, target: str, amount: int) -> None:
    if target not in balances:
        raise KeyError(target)
    _debit(balances, source, amount)
    balances[target] += amount


def withdraw(balances: dict[str, int], account: str, amount: int) -> None:
    _debit(balances, account, amount)
