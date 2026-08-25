---
name: fix
description: Repair evident defects directly and use focused diagnosis only when the cause is unknown.
---

# fix

Own the repair end to end unless it reaches an Owner, authority, protected-action, or external-prerequisite gate.

## Establish the target

Use the request, reproduction, accepted decisions, tests, and current behavior to establish the expected result. Inspect enough evidence to find the cause, smallest coherent repair, changed surfaces, and useful verification. Use `../cto/SKILL.md` as the technical controller.

Resolve routine ambiguity from accepted product scope and evidence. If the defect exposes new product scope or an Owner choice about vision, audience, portfolio priority, cost, or risk, use `../../product/shape/SKILL.md`. Resume authorized repair after the decision. Do not ask Owner for implementation choices or create tracking, product review, or approval ceremony for routine details.

## Repair an evident cause

Use normal execution when the cause is clear:

1. Confirm the faulty behavior when practical.
2. Apply the smallest coherent repair.
3. Run evidence that proves the affected behavior.
4. Finish without an issue, campaign, independent review, or regression test unless the changed surface or repository policy requires it.

Add regression coverage only when a stable seam captures meaningful behavior. Rendered output and affected checks may be enough for a visual correction. Apply the technical policy's finding lifecycle and verification-gap check. Do not absorb nearby work.

## Diagnose an unknown cause

If the cause is unclear, read `../diagnose/SKILL.md`. For diagnosis-only, report the proven cause without mutation. When repair is authorized, return the cause and evidence to the controller and continue execution.

Campaign requires coordination or recovery state that must survive a session, wait, or interruption. Bounded parallel repair stays `EXECUTE`. Changed surfaces and independent lanes affect evidence or delegation, not campaign selection.

Read `../../trackers/github-task/SKILL.md` only for accepted tracked work, requested persistence, or repository-required lifecycle. Decide that an independent finding is `PERSISTED` before loading its tracker to search for a duplicate and save it.

Revalidate only evidence invalidated by the repair. Finish with proof for the delivered state. Escalate only an Owner decision, protected action, missing authority, irreversible external action, or unavailable prerequisite.
