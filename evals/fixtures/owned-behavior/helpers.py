"""Date and time helpers."""

from datetime import date, datetime


def parse_iso(text: str) -> date:
    return datetime.strptime(text, "%Y-%m-%d").date()


def days_between(start: date, end: date) -> int:
    return (end - start).days


def format_invoice_date(value: date) -> str:
    return value.strftime("%d %b %Y")
