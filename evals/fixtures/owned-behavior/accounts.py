"""Account status rules. This module owns what makes an account terminated."""


def is_terminated(account: dict) -> bool:
    return account["status"] in {"terminated", "closed"} or account.get("closed_at") is not None
