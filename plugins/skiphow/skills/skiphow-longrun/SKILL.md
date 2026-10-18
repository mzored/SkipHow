---
name: skiphow-longrun
description: Deliver an accepted epic, milestone, or issue set through delegated slices that the CTO sequences, reviews in proportion to consequence, integrates, and carries to the agreed destination. Use for sustained execution and resumes of tracked work. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow longrun

Deliver every authorized outcome in the requested work set to its agreed destination. Before consequential work, and again after any context compaction, load the [SkipHow CTO kernel](../skiphow/SKILL.md) by invoking the `skiphow` skill where the host has a skill tool, otherwise by reading it, unless its full text is already in context; a summary is not its text. The lead stays the accountable CTO throughout.

## Starting and resuming

Use [tracked work](../skiphow/references/tracked-work.md) to reconcile current records, accepted decisions, live branches, ownership, and prior delivery before starting or resuming. Retire superseded instructions in execution records that no live session is writing. Leave a live session's lane to it, and keep independent authorized work moving around it and around pending owner decisions.

## Slices

Use [delegation](../skiphow/references/delegation.md) to size and sequence verifiable slices and to route each one. Scope, product decisions, synthesis, integration, and the completion claim stay with the lead. Reassess routing or split an assignment when a miss, growing scope, or context pressure makes its current shape unreliable. Run ready independent slices in parallel only within verified writer isolation and integration capacity. Without that isolation, say so and keep the lead as the only writer while delegates investigate or review. When delegates are unavailable, carry safe implementation directly.

Before accepting a slice into the lead's working state, check the return against the current state and review it at the depth its consequence warrants. [Review](../skiphow/references/review.md) says where independent review earns its cost and when to stop; a routine slice needs no fresh reviewer. If a slice warranted independent review and none was available, report that review as `UNVERIFIED` instead of calling the slice reviewed.

## Integration and closure

Use [integration](../skiphow/references/integration.md) to combine accepted results, check them together, and choose delivery units. A slice's handoff to the lead and the owner's delivery can have different destinations. Close a record only when its own promised outcome holds, as [tracked work](../skiphow/references/tracked-work.md#closing-what-the-tracker-carries) describes; accepting a handoff does not close an outcome still waiting for delivery. An implementation report or a review verdict alone does not establish delivery.

## When progress goes wrong

Use [diagnosis](../skiphow/references/diagnosis.md) when a test, delegate, tool, or integration behaves oddly, progress stops producing signal, or the same failure returns. When the cause is the delivery system, fix it under [testing](../skiphow/references/testing.md) for slow or flaky checks and integration for CI and release paths. Change direction when the evidence says to, and keep independent outcome-producing work moving. Watch the whole run for the kernel's warning signs, such as test or tooling code outgrowing the product or review loops getting longer, because they build up across slices that each looked reasonable.

## Continuity

Checkpoint through the project's tracking and continuation conventions at meaningful boundaries, so a pause or a lost context loses no accepted work. On pause, record what is in flight and what resumes it under tracked work. Keep going past slice handoffs until every authorized outcome is verified at its agreed destination or has a concrete recorded blocker. Production and public releases keep the kernel's explicit-grant boundary.

Report delivered outcomes and how they were checked, accepted results still waiting for delivery, remaining review or owner actions, and owned resources that could not be retired.
