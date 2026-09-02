# Delegation

Use this before dispatching a delegate, and for work run across several units. [Decomposition](decomposition.md) settles what the units are. This is how they run.

## Running the units

Run the work as a graph, not a list. Take the blocking edges [decomposition](decomposition.md) established, or read them off work that arrived already split. A part is ready when nothing it needs is outstanding, whatever order you imagined for it.

Readiness is not capacity. Start only ready units that the run can keep isolated, integrate as each lands, and revalidate against current live state without sibling work invalidating their evidence. Recompute the ready set and the available capacity after each result. A lane that has stopped making measurable progress is stopped and diagnosed, not waited on. Do not wait for a whole tier, and do not fill every ready lane merely because it exists.

Serialize parts that would change the same shared surface even when nothing else blocks them. Concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save.

## The brief

A delegate carries one outcome it can demonstrate on its own, verifiable alone and reviewable in one pass. Do not hand one delegate several. One handed an open-ended body of work runs until it exhausts its room.

Give each delegate four things: the outcome it owns, what would show that outcome true, the boundary it works inside, and the instruction to come back with a blocking unknown instead of settling it alone. The boundary names what the delegate must not touch and which authority it does not carry.

A delegate knows only what its brief says, so a rule you did not write into the brief does not reach it. A delegate that cannot state its own completion condition will invent one. Rules and the completion condition belong in the brief. The material they apply to is pointed at, not copied: name the record, the prior change, or the file to read. Repeating context into every brief multiplies cost and lets briefs drift from the source.

## The level each delegate runs at

Match the capability and effort each delegate runs at to its own work rather than to whatever the host would pick for it. The session runs on what the owner chose. A delegate runs on what its own work needs, named explicitly. Check what this host does with a delegate whose level is unset before relying on it. Where the default is to inherit the session, saying nothing is not neutral: the level chosen for the hardest judgment in a request silently becomes the floor for every mechanical lane under it.

Match the level to what the work demands, not to how important the change feels.

- Bounded mechanical work against a stated specification runs at the cheapest level that can complete it. A named edit, an inventory, extracting facts from logs or test output, a duplicate check.
- Work that carries a settled design into code, or fits an existing pattern across several files, runs at the ordinary level.
- Work that decides something runs at the strongest level available. Architecture, an unknown cause, a security or contract judgment, build against reuse.
- Anything that reviews, judges, or decides runs at no less than the session dispatching it, because a weaker check reports agreement rather than finding what you missed.

A weaker level on ambiguous work can spend more turns than the level it saved, and return something that reads finished. Where a brief cannot state its own completion condition precisely, raise the level or split the work rather than routing it down. Routing down is a judgment about how well the work is specified, not a budget target.

Hosts expose this differently, so read the control the current one actually offers instead of assuming. Where a host takes a per-delegate model, name it. Where it takes only a reasoning or effort setting, that setting carries the routing and the levels above collapse onto it. Where it exposes no per-delegate control at all, the levels are not available and the choice is only whether to delegate.

## What comes back

What comes back matters as much as what goes out. Where the output is long, have the delegate leave it in the host's own working area rather than the project, and return its verdict, its findings, and the path. Every finding still comes back. It is the bulk that stays behind. Pulling entire reports into the context that dispatched them undoes the isolation the delegate was for.

A returned question is yours to settle, not to forward. Answer it from the project, the records, or your own technical judgment. Carry it to the owner only under the same bar as any other question: a material product choice the available evidence cannot settle, a protected action, or something only a person can do. Fifteen lanes returning questions is not fifteen questions for the owner.

A delegate returns its result and evidence. Integrating the work, disposing of findings, and judging completion stay with the root request. Keep integration reviewable: bring each result back and confirm it against the current state rather than trusting a report. Reviewing each unit as it lands is also what keeps review affordable, because the alternative is one pass over everything at the end.

## Reconciling the set

Track every unit you accepted through to a named end, and reconcile the set against the request rather than against your memory of the run. A named end includes the working state the unit created. Once its result lands, reconcile its branch and isolated checkout under [finishing a branch](finishing-a-branch.md), and report any state that could not be retired. Do not call the set finished while integrated working state remains unaccounted for.

Leaving a unit for later needs a reason the owner would accept. It is blocked, it needs a decision only they can make, or its authority was never granted. It also needs a record carrying what the work already established. Preferring not to do it is not such a reason, and a unit quietly absorbed into another is not finished. This is the failure that grows with the number of units.

## Isolation

Lanes that write at the same time need separate working trees. Concurrent delegates in one checkout read each other's half-finished edits, run checks against a state no unit owns, and make a commit of only owned changes impossible. Isolate them, or run them one at a time.

Nothing here requires a branch, worktree, pull request, or review stage. Use those only when the request's authority and the repository's own conventions call for them.

When isolation is warranted, where it lands matters as much as that it exists. Prefer the host's own worktree mechanism, which owns placement and cleanup. Otherwise put the worktree in the location this repository already ignores, and confirm it is ignored before creating anything there rather than assuming. Only when the repository has no such location, use a directory under the temporary area. Never create a worktree beside the repository or anywhere else outside it. A sibling directory is invisible to the project's own ignore rules and cleanup, and it accumulates until someone finds it by accident. Do not edit ignore rules merely to make room for isolation.

Confirm each lane is in a checkout of its own before it writes, by having it report the path it is working in and the commit it starts from. An isolation mechanism that reports success while handing back the shared checkout is the failure isolation exists to prevent. It turns an instruction that would be harmless in a worktree, such as resetting to a base, cleaning the tree, or switching branches, into one that destroys whatever else was there. Isolation is not total either: separate worktrees share one stash stack, so a stash pushed in one is visible and poppable from the others.
