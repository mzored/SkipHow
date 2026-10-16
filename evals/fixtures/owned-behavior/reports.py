"""Synthetic overdue report."""

import helpers


def overdue_days(due: str, today: str) -> int:
    return max(0, helpers.days_between(helpers.parse_iso(due), helpers.parse_iso(today)))
