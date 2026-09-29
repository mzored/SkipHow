---
name: skiphow-fast-fixes
description: Coordinate a live stream of local fixes and feedback before delivery, across interfaces, services, scripts, configuration, and artifacts. Use for bounded changes that may arrive while others run, with proportional delegation, focused checks, and recoverable shown results. A request to ship uses the delivery workflow.
---

# SkipHow fast-fixes

Give the owner checked local results to inspect and revise while continuing independent accepted work. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. The lead remains the accountable CTO; showing one result completes that iteration, not the rest of the session's work.

## Coordinate incoming work

Use [delegation](../skiphow/references/delegation.md) to handle arriving requests, changed assignments, dependencies, isolation, and returns. Keep simple work direct and group related tiny fixes. Delegate independent investigation, implementation, or review when it reduces expected completion cost or useful latency within the owner's constraints. Keep the lead available to reconcile messages and results instead of tying it up in lengthy implementation that a delegate could usefully carry. A message is not automatically a separate task or agent.

Resolve engineering choices yourself. Use [product](../skiphow/references/product.md) for genuinely open product choices and plan only as much as the affected outcome needs. Continue independent work while an answer is pending. Keep all accepted work accounted for through [tracked work](../skiphow/references/tracked-work.md), without a separate ticket for every small edit.

## Preserve and show local results

Discover the project's working base, isolation, preservation, and inspection conventions. Reuse this session's owned workspace; in a Git project, use an isolated branch and worktree where needed to preserve other work. A project without Git or a browser result needs neither initialized version control nor a server for this workflow. Verify writer isolation and coordinate shared runtime resources under delegation; without safe isolation keep the lead as the only writer. Without delegates, work directly where the required review remains possible and report unavailable independent review.

Use [integration](../skiphow/references/integration.md) to combine accepted results locally and [verification](../skiphow/references/verification.md) to check and review the combined state. Show coherent results as they become ready, naming what changed and its evidence. For an interface, inspect the rendered result and show the actual preview through a usable address or host tool; for other work, demonstrate the relevant behavior or inspect the resulting artifact. Report an unavailable inspection as a gap rather than claiming it happened. Continue other accepted work after showing a result; wait when none can safely advance or the owner asks to pause or wait.

Before an edit or integration supersedes a shown state, preserve that state as a local checkpoint, even when feedback asks to revise it. In Git, commit only owned changes through the permitted commit path; elsewhere use the project's or host's safe recoverable mechanism. A message alone needs no checkpoint, and isolated work need not wait for one. If preservation is blocked, keep the shown state intact and continue only work independent of that transition. An explicit instruction to discard or exclude a change takes precedence. Keep owned resources needed for continued inspection available and retain the minimal recovery association under tracked work.

## Verification and delivery boundary

Choose focused checks for the changed behavior by their evidence, cost, and effects, not by tool name. A targeted unit, API, CLI, or browser test can be appropriate. Defer full delivery gates until delivery while honoring mandatory project checks and explicit owner restrictions. Inspect commands and hooks before running them; if a required path conflicts with those restrictions, preserve the work and report the conflict without bypassing the hook or running the forbidden check. Name any remaining verification gap.

Feedback and acceptance keep this session in iteration mode and do not trigger push, shared integration, or delivery gates. On a delivery request such as deploy-ready or clean, use [deploy-ready](../skiphow-deploy-ready/SKILL.md) to reconcile the delivery set, including in-flight work, and carry it through deferred checks and authorized delivery. Production still needs its applicable explicit grant. On pause or resume, preserve and reconcile accepted work, the shown state, pending feedback, resources, and remaining verification through tracked work. Handle new messages when the host delivers them; do not claim background execution or automatic resumption that the host does not provide.
