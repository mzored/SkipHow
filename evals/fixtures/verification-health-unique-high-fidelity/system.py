"""Synthetic system whose defect appears only across the complete round trip."""

from __future__ import annotations

import json
from pathlib import Path


def serialize(value: str) -> str:
    return json.dumps({"configured": value})


def persist(payload: str, destination: Path) -> None:
    destination.write_text(payload, encoding="utf-8")


def restart_and_read(source: Path) -> str:
    persisted = json.loads(source.read_text(encoding="utf-8"))
    return persisted.get("value", "default")
