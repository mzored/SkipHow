# Delegation

Open this for sizeable independent work, parts that land, verify, or review separately, or delegate returns to reconcile.

## Whether to split at all

Work directly when that costs less than describing, dispatching, and integrating parts.

Prefer units that deliver an outcome someone can verify end to end. Split when the split buys something: easier review, a safer rollback or migration, an order integration must follow, separate ownership, context that will not fit one pass, staged delivery, verification that runs on its own, or isolating a wide mechanical change from work that carries judgment. One outcome is still worth splitting when one of those applies, and length alone is not one of them.

## The size of a unit

A layer, schema, interface, endpoint, or screen alone may not be a demonstrable outcome; as a heuristic, not a law, prefer one across layers.

Size the unit for implementation, verification, and review together, using existing measurements or a cheap sample where its breadth is uncertain. A step with no independently verifiable result stays inside a unit.

For an interface migration, add the compatible form, migrate consumers in batches, then remove the old form. Independent repairs can form separately verifiable groups around real dependencies, coordinating shared definitions. A wide uniform transformation may cost less as one automated change.

Where a split is risky or tightly coupled, an independent check can earn its cost. Look for unverifiable units, invented dependencies, prescribed implementation, duplicate work, and uncovered outcomes. Elsewhere no split review is required.

## Order and readiness

A unit is blocked when it needs another's result; record those edges. It is ready when none remain, regardless of preferred order. Readiness is not capacity: start only ready units you can isolate and integrate as each lands.

Serialize parts that would change the same shared surface even when nothing else blocks them: concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save. The kernel's isolation rule decides whether a delegate may write at all.

Decompose to the next verifiable outcome, leaving later units provisional where earlier results can change them.

As messages arrive, distinguish additions, revisions, cancellations, and a session-wide pause. Preserve accepted work, update affected assignments and dependencies, and stop or redirect obsolete work through available host controls. Cancellation affects its dependent work; a pause stops further dispatch and uses available controls to stop active work, preserving partial results and reporting anything still running. Continue independent work unless the owner paused the session.

## Whether to delegate at all

Keep simple, tightly sequential, or shared-context work and checks needed immediately. Delegate sizeable independent work, parallel investigation, contained specialist judgment, or work whose bulk belongs outside this context, when its return can be checked. Availability alone does not justify dispatch.

## The brief

Use the kernel's brief contract; implementation stays the delegate's judgment unless the task requires otherwise. For lengthy work, [diagnosis](diagnosis.md#long-work-that-stops-producing-evidence) supplies observable progress and return conditions. An outgrown assignment returns preserved work, evidence, and remaining scope. Checkpoints follow project rules; commits alone do not measure progress.

Supply assignment-specific rules and completion evidence absent from the host's context. Point to their source record, prior change, or file instead of copying it.

## The level each delegate runs at

Choose the lead's and each delegate's model and effort separately to minimize expected total cost with a credible chance of meeting acceptance in one pass. Include retries, latency, verification, correction, and integration within the owner's token, spending, and latency constraints. Compare model and effort independently: a stronger model at lower effort can cost less per accepted result than a cheaper model at higher effort. Models and effort have no assumed total order; the parent's setting is neither floor nor ceiling. Judge reasoning, ambiguity, context breadth and interactions, error consequences and detectability and reversibility, and the cost and independence of the lead's verification. Task labels do not determine capability; ordinary routing needs no new benchmark or persistent state.

Preserve a route shown adequate for comparable work unless evidence justifies a change; root status, orchestration, duration, and available stronger settings are not evidence. Favor a cheaper sufficient route for bounded work with explicit acceptance, contained context, and errors cheap to detect and repair. Use greater capability when it materially improves acceptance, especially with ambiguity or errors costly to detect, integrate, or undo. High consequence alone does not require the strongest model when independent verification catches mistakes cheaply; routine-looking work can need more when failures are hard to observe.

Keep an escalation local to the assignment that needs it and reconsider the route for simpler follow-up work. Use actual task consumption where available; API list prices, cached-input charges, and subscription allowances measure different things, and unavailable costs stay unknown.

After a miss, identify what limited the result: capability or effort, the brief, task or context size, missing evidence or tools, or the boundary. Change the cheapest responsible factor; an unclear completion condition needs a clearer brief, not escalation. Repeat only with a justified change; there is no fixed escalation count.

Naming a model or effort does not set it. Use host controls, whether separate, preconfigured, or inherited; read effective settings back where exposed. A model override proves no effort override. Report unavailable controls or hidden settings, and count inheritance-only routing when weighing delegation.

A delegate that can dispatch its own may lack this guidance, and its delegates often inherit its route. The brief's bound on nested fan-out, which may be none, keeps cost the lead cannot see from multiplying.

Verify a writer's distinct workspace and starting state from its own environment; otherwise keep delegates read-only and the lead the only writer. Tests can mutate shared resources even without source edits: isolate or serialize conflicting operations on services, databases, ports, and outputs.

## Where isolation lands

Prefer host-managed worktrees and cleanup. Otherwise verify an ignored in-project location, creating and ignoring one if absent. Separate worktrees share a stash stack. Give writers the applicable shared-resource constraints: preserve work in lane-owned state or coordinate shared operations. An unqualified stash pop can consume another lane's work. Capture and verify your own checkpoint's immutable identity without racing a shared latest pointer, or serialize the operation; restoration and cleanup must preserve other lanes' entries too.

## What comes back

Convey status, checked result identity, acceptance summary with [verification records](verification.md#reusing-a-verification-record), every finding and blocker, and accessible detail references in the brief. Keep decision facts inline and bulk reports, logs, inventories, and histories in the host's working area. Reuse artifacts; small results need no report file. Preserve all findings and uncertainty.

Carry this boundary through briefs, review inputs, and return checks; pass bulk directly by reference. The lead inspects reusable verification records, widening for risk, contradiction, or missing proof; a verdict or pointer alone is not acceptance. Corrections return changes, current evidence, and all unresolved findings and blockers rather than the whole history.

Settle returned technical questions from project evidence and your judgment, without passing them to the owner. A problem a delegate returns is one you found.

Check each returned result and its evidence against current intent as it arrives; a superseded result cannot overwrite accepted revisions or restore cancelled behavior. A handoff alone requires no pull request or publication; the lead chooses delivery units under [integration](integration.md), whose boundaries may differ from assignments.

## Reconciling the set

Track every unit you accepted through to a named end. A named end includes the working state the unit created, so report what could not be retired.

Defer a unit only for a blocker, an owner decision, or missing authority, recording what the work established. Absorbing it into another unit does not finish it.

Where the request authorizes it and the project keeps tracked work, record the split there rather than only in the conversation, under [tracked work](tracked-work.md).
