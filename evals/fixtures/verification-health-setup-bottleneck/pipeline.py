"""Synthetic recurring-cost model derived from retained CI timings."""

from __future__ import annotations


def recurring_setup_seconds(measured: dict[str, int], plan: dict[str, object]) -> int:
    cost = 0
    if not plan["reuse_test_data"]:
        cost += measured["test_data_preparation"]
    if not plan["reuse_prepared_environment"]:
        cost += measured["dependency_installation"]
    if not plan["reuse_started_services"]:
        cost += measured["service_startup"]
    return cost
