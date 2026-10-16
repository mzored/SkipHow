"""Synthetic charges in integer units."""

from accounts import is_terminated


def charge(account: dict, amount: int) -> dict:
    if is_terminated(account):
        raise PermissionError("account is terminated")
    if amount <= 0:
        raise ValueError("amount must be positive")
    return {"account": account["id"], "amount": amount}
