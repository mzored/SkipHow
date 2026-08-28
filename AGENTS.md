# Repository instructions

These are contributor rules for developing SkipHow. They do not describe how SkipHow behaves at runtime; that lives in `plugins/skiphow/` and is the thing under test here. Do not use an installed SkipHow plugin to govern work on this repository.

## Product direction

Treat the README as the product brief. SkipHow is a small, provider-independent instruction layer for strong agents, not a workflow engine. Its product shape is one plain-language owner skill backed by a thin autonomous kernel and a library of focused internal methods. Preserve autonomous technical judgment, effort proportional to the request, and the least process that reliably reaches a verified result.

Keep universal runtime policy in the owner kernel as outcomes, authority boundaries, and non-negotiable invariants. Put reusable task discipline in narrow referenced method files and load only what materially helps. Methods are not routes, commands, roles, or an owner-operated chain. Leave sequencing, tools, decomposition, and implementation to the agent unless evidence shows that judgment is unreliable. Audit briefs, checklists, past transcripts, and one-off preferences are evidence for the question they examine; they are not standing product requirements.

## Changing the runtime contract

Change the shipped instructions to fix an observed defect or protect a high-risk boundary, not to describe an ideal execution in full. One run can prove that wording is missing, ambiguous, or contradictory. It cannot prove that agents generally need a new procedure.

Prefer deleting a contradiction, clarifying intent, or moving a discipline into a focused method over adding universal policy. Add a mandatory step, role, gate, dependency, or persistent state only when evidence shows that capable agents cannot reliably infer the needed behavior and the benefit justifies its ongoing cost. Remove obsolete or redundant text when a rule changes. Review added policy for lost autonomy, extra turns, and provider assumptions as seriously as any functional regression.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance. Read `docs/decisions.md` before changing the product contract so old alternatives are not reopened without new evidence. The immutable 2.0.1 links in that file preserve the full earlier ADR and research archive.

Model behavior is proven only by deliberate receipts from real runs made with the host's own permission and budget controls. Summarize claims and durable source links in `docs/evidence.md`; do not add one research file per run or release. A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

## Checks

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. Before completion, run `python scripts/check.py` and `git diff --check`. For packaging changes, also run `python scripts/check_hosts.py` and report an unavailable host as `UNVERIFIED`. `scripts/check.py` validates the single owner skill, all reachable internal methods and resources, the continuity hook, aligned versions, and portability boundaries such as personal paths and versioned model IDs. Change the check and `docs/decisions.md` together when those invariants change; do not pin a method roster, role set, or prose budget.

## Portability and safety

Do not add personal paths, home-directory assumptions, credentials, telemetry, or network calls to the package or its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
