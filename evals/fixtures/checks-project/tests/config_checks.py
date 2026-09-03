"""Checks for the example project's configuration.

Run with: python scripts/project_checks.py

The module is deliberately not named test_*.py, so that a bare pytest run in
the SkipHow repository never collects this fixture.
"""

from app.config import Config


def test_defaults_are_present() -> None:
    config = Config()
    assert config.timeout_seconds > 0
    assert config.endpoint.startswith("https://")
