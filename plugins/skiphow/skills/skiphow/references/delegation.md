# Delegation

Use this to run work through delegates or across several units. [Decomposition](decomposition.md) settles what the units are; this is how they run.

Run the work as a graph, not a list. Take the blocking edges [decomposition](decomposition.md) established, or read them off work that arrived already split. A part is ready when nothing it needs is outstanding, whatever order you imagined for it. Start everything ready and reopen the set as each unit lands. Waiting for a whole tier to finish before opening the next one wastes most of the concurrency.

Serialize parts that would change the same shared surface even when nothing else blocks them. Concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save.

Give each delegate the outcome it owns, what would show that outcome true, the boundary it works inside — what it must not touch, and which authority it does not carry — and the instruction to come back with a blocking unknown instead of settling it alone. A delegate knows only what its brief says, so a rule you did not write into the brief does not reach it. A delegate that cannot state its own completion condition will invent one. Rules and the completion condition belong in the brief; the material they apply to is pointed at, not copied. Name the record, the prior change, or the file to read. Repeating context into every brief multiplies cost and lets briefs drift from the source.

Match the capability and effort each delegate runs at to its own work rather than to whatever the host would pick for it; [model routing](model-routing.md) settles that.

What comes back matters as much as what goes out. Where the output is long, have the delegate leave it in the host's own working area rather than the project, and return its verdict, its findings, and the path. Every finding still comes back; it is the bulk that stays behind. Pulling entire reports into the context that dispatched them undoes the isolation the delegate was for.

A returned question is yours to settle, not to forward. Answer it from the project, the records, or your own technical judgment. Carry it to the owner only under the same bar as any other question: a material product choice the available evidence cannot settle, a protected action, or something only a person can do. Fifteen lanes returning questions is not fifteen questions for the owner.

A delegate returns its result and evidence. Integrating the work, disposing of findings, and judging completion stay with the root request. Keep integration reviewable: bring each result back and confirm it against the current state rather than trusting a report. Reviewing each unit as it lands is also what keeps review affordable, because the alternative is one pass over everything at the end.

Track every unit you accepted through to a named end, and reconcile the set against the request rather than against your memory of the run. A named end includes the working state the unit created. Once its result lands, reconcile its branch and isolated checkout under [finishing a branch](finishing-a-branch.md), and report any state that could not be retired. Do not call the set finished while integrated working state remains unaccounted for. Leaving a unit for later needs a reason the owner would accept — it is blocked, it needs a decision only they can make, or its authority was never granted — plus a record carrying what the work already established. Preferring not to do it is not such a reason, and a unit quietly absorbed into another is not finished. This is the failure that grows with the number of units.

Lanes that write at the same time need separate working trees. Concurrent delegates in one checkout read each other's half-finished edits, run checks against a state no unit owns, and make a commit of only owned changes impossible. Isolate them, or run them one at a time.

Nothing here requires a branch, worktree, pull request, or review stage. Use those only when the request's authority and the repository's own conventions call for them.

When isolation is warranted, where it lands matters as much as that it exists. Prefer the host's own worktree mechanism, which owns placement and cleanup. Otherwise put the worktree in the location this repository already ignores, and confirm it is ignored before creating anything there rather than assuming. Only when the repository has no such location, use a directory under the temporary area. Never create a worktree beside the repository or anywhere else outside it: a sibling directory is invisible to the project's own ignore rules and cleanup, and it accumulates until someone finds it by accident. Do not edit ignore rules merely to make room for isolation.

Confirm each lane is in a checkout of its own before it writes, by having it report the path it is working in and the commit it starts from. An isolation mechanism that reports success while handing back the shared checkout is the failure isolation exists to prevent, and it turns an instruction that would be harmless in a worktree — resetting to a base, cleaning the tree, switching branches — into one that destroys whatever else was there. Isolation is not total either: separate worktrees share one stash stack, so a stash pushed in one is visible and poppable from the others.
