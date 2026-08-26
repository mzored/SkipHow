# Repository instructions

These are contributor rules for developing SkipHow. They do not describe how SkipHow behaves at runtime; that lives in `plugins/skiphow/` and is the thing under test here. Do not use an installed SkipHow plugin to govern work on this repository.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance rather than older notes in this repository. Accepted decisions in `docs/decisions/` and notes in `docs/research/` are evidence with a date, not constraints: confirm, revise, or supersede them with a new ADR when current evidence supports it.

Model behavior is proven only by receipts under `docs/research/<date>/` from real runs made on purpose with the host's own permission and budget controls (ADR 0008). A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

## Checks

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. Before completion, run `python scripts/check.py` and `git diff --check`. For packaging changes, also run `python scripts/check_hosts.py` and report an unavailable host as `UNVERIFIED`. `scripts/check.py` encodes the currently accepted package shape (one skill, its references, the agent adapters, the continuity hook, word budgets, no personal paths or versioned model IDs); change the check together with the ADR when the shape changes.

## Portability and safety

Do not add personal paths, home-directory assumptions, credentials, telemetry, or network calls to the package or its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
