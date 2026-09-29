# Delegation

Open this when work holds a sizeable independent piece a delegate could carry, when its parts would land, be verified, or be reviewed separately, or when a delegate's results have to come back and be reconciled.

## Whether to split at all

Work directly when that costs less than describing, dispatching, and integrating parts.

Prefer units that deliver an outcome someone can verify end to end. Split when the split buys something: easier review, a safer rollback or migration, an order integration must follow, separate ownership, context that will not fit one pass, staged delivery, verification that runs on its own, or isolating a wide mechanical change from work that carries judgment. One outcome is still worth splitting when one of those applies, and length alone is not one of them.

## The size of a unit

Prefer a demonstrable outcome across layers. A layer, schema, interface, endpoint, or screen alone may not be one. This is a heuristic, not a law.

Size the unit for implementation, verification, and review together, using existing measurements or a cheap sample where its breadth is uncertain. A step with no independently verifiable result stays inside a unit.

For an interface migration, add the compatible form, migrate consumers in batches, then remove the old form. Independent repairs can form separately verifiable groups around real dependencies, coordinating shared definitions. A wide uniform transformation may cost less as one automated change. Parallelism still depends on isolation and integration capacity.

State the outcome, its proof, and the allowed surface. Implementation stays the delegate's judgment unless the task requires otherwise.

Where a split is risky or tightly coupled, an independent check can earn its cost. Look for unverifiable units, invented dependencies, prescribed implementation, duplicate work, and uncovered outcomes. Elsewhere no split review is required.

## Order and readiness

A unit is blocked when it needs another's result, and not when you would rather do it first. Record only those edges; a part is ready when nothing it needs is outstanding, whatever order you imagined for it. Readiness is not capacity: start only ready units you can keep isolated and integrate as each lands.

Serialize parts that would change the same shared surface even when nothing else blocks them: concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save. The kernel's isolation rule decides whether a delegate may write at all.

Decompose to the next verifiable outcome, leaving later units provisional where earlier results can change them.

As messages arrive, distinguish additions, revisions, cancellations, and a session-wide pause. Preserve accepted work, update affected assignments and dependencies, and stop or redirect obsolete work through available host controls. Cancellation affects its dependent work; a pause stops further dispatch and uses available controls to stop active work, preserving partial results and reporting anything still running. Continue independent work unless the owner paused the session.

## Whether to delegate at all

Keep simple, tightly sequential, or shared-context work and checks needed immediately. Delegate sizeable independent work, parallel investigation, contained specialist judgment, or work whose bulk belongs outside this context, when its return can be checked. Availability alone does not justify dispatch.

## The brief

Use the kernel's brief contract. For lengthy work, [diagnosis](diagnosis.md#long-work-that-stops-producing-evidence) supplies observable progress and return conditions. An outgrown assignment returns preserved work, evidence, and remaining scope. Checkpoints follow project rules; commits alone do not measure progress.

Supply assignment-specific rules and completion evidence absent from the host's context. Point to their source record, prior change, or file instead of copying it.

## The level each delegate runs at

Choose the lead's and each delegate's model and effort separately, for the lowest expected total cost of a verified acceptable outcome with a credible chance of meeting the lane's acceptance bar in one pass. That cost includes retries, latency, verification, correction, and integration, within the owner's token, spending, and latency constraints. Compare model and effort independently: a more capable model at reduced effort can cost less per accepted result than a cheaper model at greater effort. No total order across models and effort levels is assumed, and the parent's setting is neither a floor nor a ceiling. Judge the reasoning and ambiguity involved, the breadth and interaction of context, the consequence of error and how hard it is to detect and undo, and the cost and independence of the lead's verification. Task labels such as planning, implementation, review, and diagnosis do not determine capability, and ordinary routing needs no new benchmark or persistent routing state.

Preserve a route already shown adequate for comparable work unless evidence justifies a change; root status, orchestration, duration, and stronger settings being available are not such evidence. Favor a lower-cost sufficient route when the lane is bounded, its completion condition is explicit, context is contained, and errors are cheap to detect and repair. Use greater capability when it materially improves the chance of acceptance, especially with substantial ambiguity or errors expensive to detect, integrate, or undo. High consequence alone does not require the strongest model when independent verification catches mistakes cheaply, and routine-looking work can need more when its failures are hard to observe. Access to a cheaper model does not make delegation worthwhile when direct work costs less overall.

Keep an escalation local to the assignment that needs it and reconsider the route for simpler follow-up work. Use actual task consumption where available; API list prices, cached-input charges, and subscription allowances measure different things, and unavailable costs stay unknown.

After a miss, identify what limited the result: capability or effort, the brief, task or context size, missing evidence or tools, or the boundary. Change the cheapest responsible factor; an unclear completion condition needs a clearer brief, not escalation. Repeat only with a justified change; there is no fixed escalation count.

Naming a model or effort in your own message is not setting it. Use the host's model and effort controls, which may be separate, configured ahead of dispatch, or inherited, and read the effective settings back where the host reveals them; a model override does not establish an effort override. A control left unset still resolves to some default, often the parent's route, so leaving it unset is a routing decision held to this same test. Report an unavailable control or hidden setting honestly, and where only inheritance is available, count that when deciding whether delegation pays.

A delegate that can dispatch delegates of its own may not have this guidance in context, and its delegates often inherit its route. State in the brief whether it may delegate, how widely, and at what route, or that it may not; unbounded nested fan-out multiplies cost where the lead does not see it.

Verify a writer's distinct workspace and starting state from its own environment; otherwise keep delegates read-only and the lead the only writer. Tests can mutate shared resources even without source edits: isolate or serialize conflicting operations on services, databases, ports, and outputs.

## Where isolation lands

Prefer host-managed worktrees and cleanup. Otherwise verify an ignored in-project location, creating and ignoring one if absent. Separate worktrees share a stash stack. Give writers the applicable shared-resource constraints: preserve work in lane-owned state or coordinate shared operations. An unqualified stash pop can consume another lane's work. Capture and verify your own checkpoint's immutable identity without racing a shared latest pointer, or serialize the operation; restoration and cleanup must preserve other lanes' entries too.

## What comes back

Leave bulky output in the host's working area and return the verdict, every finding, and its path. Keep the bulk out of the lead's context.

Settle returned technical questions from project evidence and your judgment, without passing them to the owner.

Delegates return the requested result and verification evidence to the lead, who checks each against current intent and state as it arrives; superseded results cannot overwrite accepted revisions or restore cancelled behavior. A handoff alone requires no pull request or publication; the lead chooses delivery units under [integration](integration.md), whose boundaries may differ from assignments.

## Reconciling the set

Track every unit you accepted through to a named end. A named end includes the working state the unit created, so report what could not be retired.

Defer a unit only for a blocker, an owner decision, or missing authority, recording what the work established. Absorbing it into another unit does not finish it.

Where the request authorizes it and the project keeps tracked work, record the split there rather than only in the conversation, under [tracked work](tracked-work.md). A read-only plan or advice request without a requested record writes nothing.
