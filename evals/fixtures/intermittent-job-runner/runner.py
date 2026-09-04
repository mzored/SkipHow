"""Synthetic ready-job ordering with a planted nondeterminism."""


def ready_names(jobs: list[tuple[int, str]]) -> list[str]:
    ready = {name for _, name in jobs}
    return list(ready)
