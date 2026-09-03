"""Runtime configuration for the example project."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Settings the application reads at startup."""

    endpoint: str = "https://example.invalid/api"
    timeout_seconds: float = 5.0
