"""Synthetic invoice summaries."""

from helpers import format_invoice_date, parse_iso


def invoice_line(number: str, issued: str) -> str:
    return f"Invoice {number}, issued {format_invoice_date(parse_iso(issued))}"
