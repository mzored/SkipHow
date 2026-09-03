# Delegation

Open this when work holds a sizeable independent piece a delegate could carry, when its parts would land, be verified, or be reviewed separately, or when a delegate's results have to come back and be reconciled.

## Whether to split at all

Splitting is judgment about the work, not a stage to perform. Where doing the work directly costs less than describing, dispatching, and integrating parts, do it and skip the split.

Prefer units that deliver an outcome someone can verify end to end. Split when the split buys something: easier review, a safer rollback or migration, an order integration must follow, separate ownership, context that will not fit one pass, staged delivery, verification that runs on its own, or isolating a wide mechanical change from work that carries judgment. One outcome is still worth splitting when one of those applies, and length alone is not one of them.

## The size of a unit

Cut through the layers rather than along them. A unit named for a layer, a schema, an interface, an endpoint, or a screen usually cannot be demonstrated alone, and one cut through them usually can. Treat that as a heuristic rather than a law.

Too small is also wrong. Something that cannot be shown true by itself is a step inside a unit, not a unit, and parts whose only boundary is the order you imagined doing them in are not units either.

A mechanical change with a wide blast radius has no honest vertical slice. Sequence it: add the new form beside the old one, move call sites in batches, then delete the old form.

State each unit as its outcome and what would show it true. Do not prescribe files, names, structure, or steps; that wastes the judgment you delegated.

Where the split is risky or tightly coupled, an independent check of it against the request earns its cost; elsewhere none is required. Such a check looks for a unit with no observable outcome, an invented dependency, a prescribed implementation, two units that would end up doing the same work, or a part of the result no unit covers.

## Order and readiness

A unit is blocked when it needs another's result, and not when you would rather do it first. Record only those edges; a part is ready when nothing it needs is outstanding, whatever order you imagined for it. Readiness is not capacity: start only ready units you can keep isolated and integrate as each lands.

Serialize parts that would change the same shared surface even when nothing else blocks them: concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save.

Decompose only as far as the next verifiable outcome, and do not invent units whose shape earlier results will change.

## Whether to delegate at all

Having a delegate available is not a reason to use one. Keep simple work, anything a handful of tool calls finishes, tightly sequential work, single-file or shared-context changes, and checks whose result you must read at once. Send out a sizeable independent piece of work, work whose bulk you want out of this context, parallel read-heavy investigation, and a bounded specialist judgment you can check on return.

## The brief

The kernel states the minimum contract every brief carries. A delegate handed several outcomes, or an open-ended body of work, runs until it exhausts its room.

A delegate knows only what its brief says, so a rule you did not write into the brief does not reach it. A delegate that cannot state its own completion condition will invent one. Rules and the completion condition belong in the brief. The material they apply to is pointed at, not copied: name the record, the prior change, or the file to read.

## The level each delegate runs at

Match each delegate's level to its own work, not to what the host would pick. Bounded mechanical work against a stated specification runs at the cheapest level that can complete it, work carrying a settled design into code at the ordinary level, work that decides something at the strongest available. Anything that reviews or judges runs at no less than the session dispatching it: a weaker check reports agreement rather than finding what you missed. Where a brief cannot state its own completion condition, raise the level or split the work instead of routing it down.

Naming the level in your own message is not setting it. Set the host's own per-delegate control. Where the host offers only a reasoning or effort setting, the levels collapse onto it; where it offers no per-delegate control, they are unavailable and the only choice is whether to delegate.

## Where isolation lands

Prefer the host's own worktree mechanism, which owns placement and cleanup. Otherwise put it where this repository already ignores, confirmed rather than assumed. The kernel's placement rule closes the list there. Isolation is not total: separate worktrees share one stash stack, so a stash pushed in one is poppable from the others.

## What comes back

Where the output is long, have the delegate leave it in the host's own working area rather than the project and return its verdict, its findings, and the path. Every finding still comes back; only the bulk stays behind. Pulling entire reports into the context that dispatched them undoes the isolation the delegate was for.

Settle a returned question from the project, the records, or your own technical judgment. Fifteen lanes returning questions is not fifteen questions for the owner.

Bring each result back and confirm it against current state rather than trusting a report. Reviewing each unit as it lands keeps integration affordable; the alternative is one pass over everything at the end.

## Reconciling the set

Track every unit you accepted through to a named end. A named end includes the working state the unit created, so report what could not be retired.

Leaving a unit for later needs a reason the owner would accept, and there are only three. It is blocked, it needs a decision only they can make, or its authority was never granted, and it needs a record carrying what the work already established. A unit quietly absorbed into another is not finished. That failure grows with the number of units.

Where the request authorizes it and the project keeps tracked work, record the split there rather than only in the conversation, under [tracked work](tracked-work.md); a request only to plan or advise records nothing.
