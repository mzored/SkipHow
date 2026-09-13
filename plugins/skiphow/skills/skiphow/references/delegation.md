# Delegation

Open this when work holds a sizeable independent piece a delegate could carry, when its parts would land, be verified, or be reviewed separately, or when a delegate's results have to come back and be reconciled.

## Whether to split at all

Splitting is judgment about the work, not a stage to perform. Where doing the work directly costs less than describing, dispatching, and integrating parts, do it and skip the split.

Prefer units that deliver an outcome someone can verify end to end. Split when the split buys something: easier review, a safer rollback or migration, an order integration must follow, separate ownership, context that will not fit one pass, staged delivery, verification that runs on its own, or isolating a wide mechanical change from work that carries judgment. One outcome is still worth splitting when one of those applies, and length alone is not one of them.

## The size of a unit

Cut through the layers rather than along them. A unit named for a layer, a schema, an interface, an endpoint, or a screen usually cannot be demonstrated alone, and one cut through them usually can. Treat that as a heuristic rather than a law.

Too small is also wrong. Something that cannot be shown true by itself is a step inside a unit, not a unit, and parts whose only boundary is the order you imagined doing them in are not units either.

A mechanical change with a wide blast radius has no honest vertical slice. Sequence it: add the new form beside the old one, move call sites in batches, then delete the old form.

State each unit as its outcome and what would show it true. The surface a delegate may touch is a boundary on its authority; which files, names, structures, or steps implement the outcome stays the delegate's judgment unless the task itself requires them.

Where the split is risky or tightly coupled, an independent check of it against the request earns its cost; elsewhere none is required. Such a check looks for a unit with no observable outcome, an invented dependency, a prescribed implementation, two units that would end up doing the same work, or a part of the result no unit covers.

## Order and readiness

A unit is blocked when it needs another's result, and not when you would rather do it first. Record only those edges; a part is ready when nothing it needs is outstanding, whatever order you imagined for it. Readiness is not capacity: start only ready units you can keep isolated and integrate as each lands.

Serialize parts that would change the same shared surface even when nothing else blocks them: concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save. The kernel's isolation rule decides whether a delegate may write at all.

Decompose only as far as the next verifiable outcome, and do not invent units whose shape earlier results will change.

## Whether to delegate at all

Having a delegate available is not a reason to use one. Keep simple work, anything a handful of tool calls finishes, tightly sequential work, single-file or shared-context changes, and checks whose result you must read at once. Send out a sizeable independent piece of work, work whose bulk you want out of this context, parallel read-heavy investigation, and a bounded specialist judgment you can check on return.

## The brief

The kernel states the minimum contract every brief carries. A delegate handed several outcomes, or an open-ended body of work, runs until it exhausts its room.

Give each delegate the assignment-specific rules and observable completion condition it needs, accounting for context the host actually supplies. Point to the material those instructions apply to rather than copying it into the brief: name the record, the prior change, or the file to read.

## The level each delegate runs at

Choose the available model and effort with the lowest expected total cost of reaching a verified acceptable outcome and a credible chance of meeting the bounded lane's acceptance bar in one pass. Include retries, latency, verification, correction, and integration in that cost. Compare model and effort independently: a more capable model at reduced effort can cost less per accepted result than a cheaper model at greater effort. Apply the owner's token, spending, and latency constraints. Preserve an adequate current route for comparable work unless evidence justifies a change; orchestration and duration alone supply no such evidence. No total order across models and effort levels is assumed, and the parent's setting is neither a floor nor a ceiling. Judge the reasoning and ambiguity involved, the breadth and interaction of context, the consequence of error, how hard it is to detect and undo, and the cost and independence of the lead's verification. Use trustworthy relevant project results when available; ordinary routing needs no new benchmark or persistent routing state. Task labels such as planning, implementation, review, and diagnosis do not determine capability.

Favor a lower-cost sufficient route when the lane is bounded, its completion condition is explicit, context is contained, and errors are cheap to detect and retry or repair. Use greater capability when it materially improves the chance of acceptance, especially with substantial ambiguity or errors expensive to detect, verify, integrate, or undo. High consequence alone does not require the strongest model when independent verification catches mistakes cheaply and reliably. Apparently routine work can need greater capability when its failures are hard to observe. First decide whether delegation repays briefing, context transfer, verification, and integration at all; access to a cheaper model does not make delegation worthwhile when direct work costs less overall.

Keep an escalation local to the assignment that needs it and reconsider the route for simpler follow-up work. Use actual task consumption where available; API list prices, cached-input charges, and subscription allowances measure different things. State which costs are known and leave unavailable costs unknown.

After a miss, identify whether capability or effort, an unclear or incomplete brief, excessive task or context size, missing evidence or tools, or the decomposition or boundary limited the result. Change the cheapest responsible factor: repair the brief, context, or tools, split the lane, or increase capability or effort when it was plausibly limiting. An unclear completion condition needs clarification of the brief, not automatic escalation. Repeat only with a justified change, and continue only while another route has a justified chance of improving the accepted outcome; there is no fixed escalation count.

Naming a model or effort in your own message is not setting it. Use the host's exposed model and effort controls, which may be separate, configured ahead of dispatch, or inherited; read the effective settings back where the host reveals them. A model override does not establish an effort override. Report an unavailable control or hidden effective setting honestly, without claiming an unverified route was applied. Where only inheritance is available, account for that constraint when deciding whether delegation still pays.

Use the controls the active host actually exposes. Treat a delegate as a writer only after verifying its distinct checkout and starting revision from the delegate's own environment. If either fact cannot be verified, keep delegates read-only and the lead as the only writer.

## Where isolation lands

Prefer the host's own worktree mechanism, which owns placement and cleanup. Otherwise put it where this repository already ignores, confirmed rather than assumed. Where it ignores no such location, create one inside the checkout and add it to the repository's ignore rules rather than placing the worktree beside the checkout or outside the project. The kernel's placement rule closes the list there. Isolation is not total: separate worktrees share one stash stack, so a stash pushed in one is poppable from the others.

## What comes back

Where the output is long, have the delegate leave it in the host's own working area rather than the project and return its verdict, its findings, and the path. Every finding still comes back; only the bulk stays behind. Pulling entire reports into the context that dispatched them undoes the isolation the delegate was for.

Settle a returned question from the project, the records, or your own technical judgment. Fifteen lanes returning questions is not fifteen questions for the owner.

Bring each result back and confirm it against current state rather than trusting a report. Reviewing each unit as it lands keeps integration affordable; the alternative is one pass over everything at the end.

## Reconciling the set

Track every unit you accepted through to a named end. A named end includes the working state the unit created, so report what could not be retired.

Leaving a unit for later needs a reason the owner would accept, and there are only three. It is blocked, it needs a decision only they can make, or its authority was never granted, and it needs a record carrying what the work already established. A unit quietly absorbed into another is not finished. That failure grows with the number of units.

Where the request authorizes it and the project keeps tracked work, record the split there rather than only in the conversation, under [tracked work](tracked-work.md). A read-only plan or advice request without a requested record writes nothing.
