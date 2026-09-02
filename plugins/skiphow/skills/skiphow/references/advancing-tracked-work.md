# Advancing tracked work

Use this when the owner asks to carry on with what the project already has on record, rather than naming one thing to do. [Tracked work](tracked-work.md) owns the life of an individual item, including claiming it and what closing it requires. This owns crossing several of them in one session and knowing when to stop.

## The frontier

The frontier is what is takeable right now: open items whose blockers are all closed, that nothing else is already working on, and that lie on the path from live state to the requested result. An item beyond that destination is out of this run's scope however ready it is. Report it as takeable and deferred rather than resolving it on the way, because a record's claim that it must come first is a proposal unless the owner set it.

Where the request names the tracker itself as the result, the records are the request and none is deferred on this ground. Recover the result their parent outcome or the product brief names, so the report can say what reached it. When what remains takeable is only machinery while the item that would reach that result waits on the owner, the report leads with that, so the owner can reshape the request. That is not a reason to stop or to take something else quietly.

Everything else is either blocked, claimed, deferred, or done. Work the frontier and nothing else, because an item you take out of order either duplicates a lane already running or builds on a result that does not exist yet.

## The order you take them in

Take items in the order the project itself records. Where the tracker carries a priority, that order is the answer and re-deriving it wastes the pass that produced it. Order settles which takeable item comes first. It does not put an item on the path, and deferring one beyond the destination is reported, not a reordering. Where the tracker carries no priority, take the oldest first.

A recorded order you believe is wrong is a reason to run [prioritization](prioritization.md) and say so, never a reason to quietly take something else. Reordering the owner's work without telling them is a product decision made in silence.

## Reconciling before you take

Reconcile the technical direction as well as the items before taking the frontier. When live state shows repeated repairs at one boundary, competing implementations of one product behavior, or growing technical and delivery machinery without new evidence of the requested result, apply [campaign direction](campaign-direction.md) before admitting more work. Supersede affected technical records and recompute the frontier before executing more of that direction. Do not reopen settled direction without one of those signals. Recorded work is evidence of intent, not proof that its technical direction is still right.

Reconcile each item before acting too. Correct an item in the record before work starts, not after, where its stated outcome no longer matches live project state. Take an item the code has already overtaken, and one the project has marked as waiting on a decision, to [tracked work](tracked-work.md), which settles both.

## Leaving the frontier

An item leaves the frontier when its outcome is demonstrated against live state and what the work established is written back into the record. Do both at that point rather than at the end of the run, and recompute the frontier as you do, because the next thing to take is often something that was not takeable a minute ago.

Closing lands on integration under the kernel's rule. In a project that integrates through review, that happens after this run has ended, so an item handed to a review is set aside rather than closed, and items waiting on it stay blocked until that change arrives. Working a dependent against a result still sitting in review is the same mistake as taking a blocked item, which is why the dependency belongs in the tracker rather than in your reading of the run.

## Running items in parallel

Independent frontier items may run concurrently, one delegate each, under [delegation](delegation.md), but independence does not prove admission capacity. Use [campaign direction](campaign-direction.md) when active work is outrunning integration and verification. Do not run two items that touch the same behavior in parallel, however independent their records claim to be. The tracker records intent, not the code they will both edit.

## What the pass may change

An item's stated outcome bounds what this pass delivers. It does not decide what may be changed, because the owner's request still decides that and a record is evidence of intent rather than authority. A material problem found while carrying an item out is disposed of under the kernel's rule for problems the work discovers, rather than absorbed into the item in hand. That is what keeps the item reviewable, and what keeps a run from becoming an open-ended sweep nobody asked for.

## Stopping and reporting

Stop when the frontier is empty, or when everything on it that reaches the result is blocked on a decision only the owner can make, an action only they can grant, or an external party. Do not stop at the first such block. Set it aside, carry on with what remains takeable and still reaches the result, and bring the accumulated questions back in one round rather than one at a time.

When nothing takeable reaches the result, the run ends there with the batch. Filling that wait with enabling work the request did not name is the failure this rule exists to prevent, and the report says what was deliberately not taken and why. Stop and diagnose a lane that has stopped making measurable progress, under [execution health](execution-health.md), rather than waiting on it.

Report the run as one reconciliation against what the owner asked for: what closed or reached review and on what evidence, what is blocked and on whom, what was newly recorded, and what is still takeable. A list of items touched is not that report, because it does not say whether the owner can now do anything they could not do before.
