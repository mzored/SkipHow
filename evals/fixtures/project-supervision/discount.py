"""Accepted whole-unit discount rule."""


def discounted(amount: int) -> int:
    return amount - amount // 10
