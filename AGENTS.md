# Repository instructions

These are contributor rules for developing SkipHow. They do not describe how SkipHow behaves at runtime; that lives in `plugins/skiphow/` and is the thing under test here. Do not use an installed SkipHow plugin to govern work on this repository.

## Product direction

Treat the README as the product brief. SkipHow is a small, provider-independent instruction layer for strong agents, not a workflow engine. Preserve one plain-language owner entry, autonomous technical judgment, effort proportional to the request, and the least process that reliably reaches a verified result.

Write runtime policy as outcomes, authority boundaries, and non-negotiable invariants. Leave sequencing, tools, decomposition, and implementation to the agent unless evidence shows that judgment is unreliable. Audit briefs, checklists, past transcripts, and one-off preferences are evidence for the question they examine; they are not standing product requirements.

## Changing the runtime contract

Change the shipped instructions to fix an observed defect or protect a high-risk boundary, not to describe an ideal execution in full. One run can prove that wording is missing, ambiguous, or contradictory. It cannot prove that agents generally need a new procedure.

Prefer deleting a contradiction, clarifying intent, or moving an existing rule to where it loads over adding policy. Add a mandatory step, role, gate, dependency, or persistent state only when evidence shows that capable agents cannot reliably infer the needed behavior and the benefit justifies its ongoing cost. Remove obsolete or redundant text when a rule changes. Review added policy for lost autonomy, extra turns, and provider assumptions as seriously as any functional regression.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance rather than older notes in this repository. Accepted decisions in `docs/decisions/` and notes in `docs/research/` are evidence with a date, not constraints: confirm, revise, or supersede them with a new ADR when current evidence supports it.

Model behavior is proven only by receipts under `docs/research/<date>/` from real runs made on purpose with the host's own permission and budget controls (ADR 0008). A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

## Checks

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. Before completion, run `python scripts/check.py` and `git diff --check`. For packaging changes, also run `python scripts/check_hosts.py` and report an unavailable host as `UNVERIFIED`. `scripts/check.py` encodes the currently accepted package shape (one skill, its references, the agent adapters, the continuity hook, word budgets, no personal paths or versioned model IDs); change the check together with the ADR when the shape changes.

## Portability and safety

Do not add personal paths, home-directory assumptions, credentials, telemetry, or network calls to the package or its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
