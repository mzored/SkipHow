---
name: fix
description: Repair broken or regressed behavior with rigor proportional to uncertainty and risk, escalating only when diagnosis, product direction, or a durable CTO campaign is warranted.
---

# fix

Treat the human as the Owner. Own the repair end to end unless it reaches a genuine product, authority, or protected-action gate.

## Establish the target

Use the request, reproduction, accepted product contracts, designs, tests, and current repository behavior to establish what should happen. Inspect enough evidence to classify the cause, blast radius, reversibility, and verification difficulty.

If the expected product behavior is genuinely ambiguous, ask the Product Director for a bounded Product Director decision based on the existing strategy, accepted scope, user journey, and available evidence. Record the decision according to repository convention and resume the repair. Do not create a tracker item, Product Contract, independent product review, or Owner approval gate for a decision that stays within accepted product scope.

Use the full `shape` workflow only when the defect exposes new product scope or a material choice about vision, audience, priority, cost, or risk that requires Owner authority. Do not ask the Owner to choose implementation details.

## Take the cheapest safe path

Use the fast-fix path only when the cause is evident and the repair is localized, reversible, low risk, and unambiguous. It must not introduce a dependency or affect architecture, public APIs, schemas, migrations, authentication, payments, privacy, security, concurrency, or shared cross-module behavior.

For a fast fix:

1. Reproduce or confirm the faulty behavior when practical.
2. Apply the repair directly.
3. Run the smallest verification that proves the affected behavior.
4. Finish without creating an issue, plan, campaign, independent review, or new regression test unless repository policy or the repair's actual risk requires one.

A test is evidence, not a ritual. Add regression coverage when a stable seam can reproduce meaningful behavior. For a visual-only correction, browser or rendered-output evidence plus affected checks may be sufficient.

## Diagnose only when needed

If the cause is unclear, read `../diagnose/SKILL.md` and follow its diagnostic loop. After proving the root cause, classify the repair again. Continue locally when the proven fix now meets the fast-path criteria.

## Increase rigor from evidence

Move into the repository's normal technical workflow when the repair no longer meets the fast-path criteria. Hand technical decisions to the CTO. Start `cto-run` only when the work needs a durable, long-running, or multi-task campaign, using the canonical workflow at `../cto-run/SKILL.md`.

When that workflow or repository policy classifies the repair as tracked GitHub development, read `../github-task/SKILL.md` and delegate only issue, board, linked-branch, Human Gate, and final reconciliation operations to it. `github-task` does not reclassify the repair or choose its engineering rigor.

Signals for higher rigor include a new dependency, cross-module behavior, architecture or subsystem-boundary decisions, public API or schema changes, migrations, authentication, payments, privacy, security, concurrency, substantial performance work, difficult verification, or multiple viable fixes with material lifetime-cost differences.

Do not create lifecycle ceremony merely because code changed. Increase rigor only when evidence shows more uncertainty, risk, reach, or verification cost. Once increased, do not return to a lighter path unless the evidence that caused the increase was disproved.

Escalate to the Owner only for an Owner decision, protected action, missing authority, irreversible external action, or prerequisite that the available tools and roles cannot resolve.
