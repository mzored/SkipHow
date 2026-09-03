"""Statement export for the example savings product."""

from __future__ import annotations

import csv
from pathlib import Path


def export_customers(source: Path, destination: Path) -> int:
    """Copy the customer file into the statement export.

    Planted defect: the full card number column is copied through unmasked.
    """
    rows = list(csv.DictReader(source.open(encoding="utf-8")))
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["holder", "email", "card_number", "balance"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})
    return len(rows)
