---
name: fix
description: Repair broken or regressed behavior through normal execution, focused diagnosis when the cause is unknown, or a durable campaign when coordination requires it.
---

# fix

Treat the human as the Owner. Own the repair end to end unless it reaches a genuine product, authority, or protected-action gate.

## Establish the target

Use the request, reproduction, accepted product contracts, designs, tests, and current repository behavior to establish what should happen. Inspect enough evidence to understand the cause, smallest coherent repair, changed surfaces, and useful verification. Use the internal CTO controller at `../cto/SKILL.md` for the repair.

If the expected product behavior is genuinely ambiguous, ask the product controller for a bounded decision based on the existing strategy, accepted scope, user journey, and available evidence. Record the decision according to repository convention and resume the repair. Do not create a tracker item, Product Contract, independent product review, or Owner approval gate for a decision that stays within accepted product scope.

Use `../../product/shape/SKILL.md` only when the defect exposes new product scope or a material choice about vision, audience, portfolio priority, cost, or risk that requires Owner authority. Do not ask the Owner to choose implementation details.

## Execute the repair

When the cause is evident, use the controller's normal `EXECUTE` path:

1. Reproduce or confirm the faulty behavior when practical.
2. Apply the repair directly.
3. Run the smallest verification that proves the affected behavior.
4. Finish without creating an issue, campaign, independent review, or new regression test unless the changed surface or repository policy requires one.

If inspection or repair exposes another material problem, validate it cheaply and give it one terminal disposition: resolve it only when inseparable from the smallest correct repair, persist or link it as independent work when actionable, or dismiss it with a reason. Do not absorb it merely because it is nearby, and do not leave it unaccounted for.

A test is evidence, not a ritual. Add regression coverage when a stable seam can reproduce meaningful behavior. For a visual-only correction, browser or rendered-output evidence plus affected checks may be sufficient.

## Diagnose only when needed

If the cause is unclear, read `../diagnose/SKILL.md` and follow its diagnostic loop. If the user asked only for analysis, report the proven cause. If the owning request includes repair, return the cause and evidence to the controller and continue through `EXECUTE`.

Use `cto-run` only when the repair has independently executable workstreams, must survive sessions or external waits, materially benefits from parallel coordination, or needs durable recovery and reconciliation. Security, data, public API, payment, infrastructure, or shared-framework impact strengthens the required evidence but does not select a campaign.

When an accepted tracked item or repository policy requires GitHub lifecycle work, read `../../trackers/github-task/SKILL.md` only after that need is established. For an independent material finding, decide `PERSISTED` first and only then load the owning tracker adapter to search for a duplicate and save it. The adapter does not reclassify the repair or choose its engineering rigor.

Do not create lifecycle ceremony merely because code changed. Revalidate only evidence materially invalidated by the repair delta, and finish with evidence for the state actually delivered.

Escalate to the Owner only for an Owner decision, protected action, missing authority, irreversible external action, or prerequisite that the available tools and roles cannot resolve.
