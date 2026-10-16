"""Synthetic comment posting."""


def post_comment(account: dict, text: str) -> dict:
    if not text.strip():
        raise ValueError("comment is empty")
    return {"account": account["id"], "text": text.strip()}
