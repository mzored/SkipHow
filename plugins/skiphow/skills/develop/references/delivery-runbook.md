# Product delivery runbook

Deliver the immutable campaign recorded in `<run-directory>/campaign.md`.

## Inputs

- The campaign goal, included tracker items, exact Product Contract revisions, exclusions, and source snapshot in `campaign.md`.
- Repository instructions and the current target repository state.
- The canonical tracker for status and acceptance evidence.

## Required work

1. Verify the campaign snapshot and record any mismatch before changing code.
2. Translate the Product Contracts into acceptance criteria. Own architecture, dependency choices, sequencing, implementation, tests, review, and integration under the CTO operating policy.
3. Keep excluded and newly approved work out of the campaign.
4. Route product ambiguity to the Product Director. Continue without the Owner when product evidence resolves it.
5. Bind completion evidence to the exact candidate commit and included tracker items.
6. For every user-visible item governed by a Product Contract, obtain a Product Director acceptance receipt for that exact candidate commit. The receipt records the Product Contract revision, candidate commit, status, evidence location, reviewer, and timestamp. A `returned` receipt includes the concrete contract mismatch and sends the work back to the CTO.

## Terminal condition

The campaign is complete only when every included item is implemented, independently reviewed where policy requires it, verified against its acceptance criteria, integrated into the target, and reconciled with the canonical tracker. Every user-visible item governed by a Product Contract must also have an exact-candidate Product Director acceptance receipt with status `accepted`. No executable lane or unaccounted mutable state may remain.

Stop affected work only for a true Owner decision, protected action, missing authority, or external prerequisite. Record the blocker and continue any independent lane.
