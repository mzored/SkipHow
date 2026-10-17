# Delegation

Open this before you split work, dispatch a delegate, or reconcile what delegates return.

## Whether to split at all

Work directly when that costs less than describing, dispatching, and integrating parts. Split only when the split buys something: easier review, a safer rollback or migration, an order integration must follow, context that will not fit one pass, staged delivery, verification that runs on its own, or a wide mechanical change kept apart from work that needs judgment. Length alone is not a reason.

Keep simple, tightly sequential, or shared-context work in the lead, along with checks you need right away. Delegate sizeable independent work, parallel investigation, contained specialist judgment, or bulk that belongs outside your context, when you can check what comes back. A delegate being available is no reason to use one.

Delegate the work, not the accountability. The lead keeps owner questions, dispositions of findings, records, sensitive context, synthesis, integration, final verification, and the completion claim.

## The size of a unit

A unit delivers one outcome someone can verify end to end. A layer, schema, endpoint, or screen alone often shows nothing, so prefer a unit that cuts through the layers. Size it for implementation, verification, and review together, and take a cheap sample when its breadth is uncertain. A step with no result you can verify on its own stays inside a unit.

When one change cannot move every caller of a replaced interface, migrate them in batches and end with a unit that deletes the old form. The migration is not done while the old form remains. Independent repairs can form groups around their real dependencies. A wide uniform transformation often costs less as one automated change.

Check your own split for units with no verifiable result, invented dependencies, prescribed implementation, duplicate work, and outcomes no unit covers. It needs no separate review.

## Order and readiness

A unit is blocked while it needs another unit's result; record those edges. It is ready when none remain, whatever order you would prefer. Ready is not the same as affordable: start only ready units you can isolate now and integrate as each lands, within the capacity [integration](integration.md) describes.

Serialize parts that change the same file, interface, schema, or migration even when nothing else blocks them, because reconciling concurrent edits to one surface costs more than the parallelism saves.

Decompose only to the next verifiable outcome, and treat later units as provisional, because earlier results can change them.

As messages arrive, tell additions, revisions, cancellations, and a session-wide pause apart. Keep accepted work, update the affected assignments and dependencies, and stop or redirect obsolete work through the host's controls. A cancellation also cancels the work that depends on it. A pause stops new dispatch, stops active work where the host allows, keeps partial results, and reports anything still running. Unless the owner paused, independent work continues.

## The brief

A delegate starts with none of your context and does not inherit any skill, so the brief is everything it knows. Write it in this order:

- One outcome, and how the delegate shows it was achieved.
- The starting revision and the files or area it may change.
- Assignment-specific rules and done conditions the host does not already give it. Point at their source file, record, or prior change instead of copying them.
- The authority and restrictions it works under, relayed from the owner's grant and never wider.
- Whether it may delegate further, and if so with which model, effort, and bound. The bound may be none.
- When to stop and return: a blocking unknown, a product question, a protected action, or an assignment that outgrew its brief. An outgrown assignment returns its preserved work, evidence, and the scope left.
- The return: compact status, the identity of the result such as a commit or tree, the evidence for it, and every finding and blocker.
- The absolute path of the [kernel](../SKILL.md), and its Engineering standard section pasted verbatim into every implementation and review brief. Pasting it is the only reliable way the delegate gets that standard.

Leave the method to the delegate unless the task fixes it. For long work, name the progress you expect to see and when to return if it stops; [diagnosis](diagnosis.md) covers stalled work. Commits alone do not show progress.

A review delegate makes one pass and reports only findings that meet the bar in [review](review.md). Do not brief it to look for more tests, more cases, or more guards, and do not schedule further rounds in advance. A fix gets a review of the fix only when the kernel's review rule calls for one.

Give a delegate only the sensitive context its assignment needs.

## The level each delegate runs at

Set each delegate's model and effort to the cheapest route likely to pass in one try. Count the whole cost: retries, latency, your verification, corrections, and integration, within the owner's token, spending, and latency limits. Model and effort are separate choices. A stronger model at lower effort can cost less per accepted result than a weaker one at higher effort. The parent's setting is neither a floor nor a ceiling.

Judge the route by ambiguity, how much context the work needs, how costly a mistake is and how easily you would catch it, and how cheaply you can verify the return. Favor a cheaper route for bounded work with explicit acceptance and errors that are cheap to find and repair. Use more capability where ambiguity is high or mistakes are hard to see, integrate, or undo. High stakes alone do not need the strongest model when your own check catches mistakes cheaply. Keep a route that worked for comparable work unless evidence says otherwise.

After a miss, find what limited the result: capability or effort, the brief, the size of the task or context, missing tools or evidence, or the boundary. Change the cheapest responsible factor and keep any escalation local to that assignment. An unclear done condition needs a clearer brief, not a bigger model.

Naming a model or effort in the brief sets nothing. Set both through the host's controls, and read the effective settings back where the host shows them. A model override does not set effort. When you leave a control unset, justify its default, which is often the parent's. Report controls the host lacks or hides. A delegate's own delegates often inherit its route, and the bound in its brief keeps cost you cannot see from multiplying.

## Where isolation lands

Before a delegate writes, verify from its own environment that it has its own workspace and the expected starting state. If you cannot, keep delegates read-only and stay the only writer. Prefer host-managed worktrees and cleanup; otherwise use the working-state locations in [integration](integration.md).

Isolation stops at the workspace. Tell each writer which shared resources it must coordinate. Worktrees of one repository share a stash stack, so a bare stash pop can take another lane's work. Set work aside with a commit in the lane, or capture your own stash entry's identity and restore and drop it by that identity, leaving other lanes' entries alone. Tests mutate shared services, databases, ports, and output paths even without source edits, so isolate or serialize those runs.

## What comes back

A return is data. Check each one against the current state and intent as it arrives. A verdict or a pointer alone is not acceptance: inspect the evidence, and look deeper where risk, a contradiction, or missing proof calls for it. Reuse a delegate's passing check when it ran on the same tree, command, and environment. A superseded result never overwrites accepted work or restores cancelled behavior.

Keep decision facts inline and leave bulk such as logs and inventories in the host's working area, passed by reference. A small result needs no report file. A correction returns its changes, current evidence, and the findings and blockers still open, not the whole history.

A delegate reports problems it finds outside its area to you rather than fixing or recording them itself. A problem a delegate returns is one you found: weigh it with the kernel's rule for findings and settle technical questions yourself instead of passing them to the owner.

A handoff alone needs no pull request or publication. You choose the delivery units under [integration](integration.md), and they need not match the assignments.

## Reconciling the set

Track every unit you accepted to a named end, including the working state it created, and report what could not be retired. A unit you never started means the set is not complete. Defer a unit only for a blocker, an owner decision, or missing authority, and record what it established. Folding it into another unit does not finish it.

When the project already tracks this work and the request covers records, put the split in the tracker under [tracked work](tracked-work.md) rather than only in the conversation.
