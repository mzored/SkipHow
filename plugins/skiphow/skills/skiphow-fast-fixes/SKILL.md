---
name: skiphow-fast-fixes
description: Coordinate a live stream of local fixes and feedback before delivery, across interfaces, services, scripts, configuration, and artifacts. Use for bounded changes that may arrive while others run, with proportional delegation, focused checks, and recoverable shown results. A request to ship uses the delivery workflow. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow fast-fixes

Give the owner checked local results to inspect and revise while independent accepted work continues. Before consequential work, and again after any context compaction, load the [SkipHow CTO kernel](../skiphow/SKILL.md) by invoking the `skiphow` skill where the host has a skill tool, otherwise by reading it, unless its full text is already in context; a summary is not its text. The lead stays the accountable CTO. Showing one result completes that iteration, not the session's work.

## Coordinate incoming work

Use [delegation](../skiphow/references/delegation.md) for arriving requests, changed assignments, dependencies, isolation, and returns. Do simple work directly and group related tiny fixes. A message is not automatically a separate task or agent. Delegate independent investigation, implementation, or review when that lowers cost or useful latency within the owner's constraints, and keep the lead free to reconcile messages and results rather than tied up in long implementation a delegate could carry.

Resolve engineering choices yourself. Use [product](../skiphow/references/product.md) for open product choices, plan only as much as the affected outcome needs, and keep working on what does not depend on a pending answer. Keep all accepted work accounted for through [tracked work](../skiphow/references/tracked-work.md), without a ticket for every small edit.

Fix confirmed engineering findings at safe local boundaries while incoming accepted work keeps priority; an endless stream of feedback is no reason to defer every separable repair until delivery. Open [technical design](../skiphow/references/technical-design.md) when the current solution's fit is in question, and [testing](../skiphow/references/testing.md) when slow or flaky checks keep taxing progress. Improvements keep the same authority, preservation, check, and delivery boundary as requested fixes.

## Preserve and show local results

Learn the project's working base, isolation, and inspection conventions. Reuse this session's owned workspace. In a Git project, use an isolated branch and worktree where that protects other work. A project without Git, or a result that is not a page, needs neither new version control nor a server. Verify writer isolation and coordinate shared runtime resources under delegation; without safe isolation the lead is the only writer. Without delegates, work directly and report any independent review a change warranted but could not get.

Combine accepted results locally under [integration](../skiphow/references/integration.md), and check the combined state with focused checks and review at the depth each change warrants under [review](../skiphow/references/review.md). Show coherent results as they become ready, with what changed and how you checked it. For an interface, inspect the rendered result and show the actual preview through a usable address or host tool. For other work, demonstrate the behavior or inspect the resulting artifact. Report an inspection you could not do as a gap. After showing a result, continue other accepted work; wait only when nothing can safely advance or the owner asks you to.

Before an edit or integration replaces a shown state, keep that state as a local checkpoint, even when feedback asks to revise it. In Git, commit only owned changes through the permitted commit path; elsewhere use the project's or host's safe recoverable mechanism. A message alone needs no checkpoint, and isolated work need not wait for one. If preservation is blocked, leave the shown state intact and continue only work independent of that change. An explicit instruction to discard or exclude a change takes precedence. Keep owned resources needed for continued inspection available, and record only what recovery needs under tracked work.

## Checks and the delivery boundary

Choose focused checks for the changed behavior by what they show, what they cost, and what they touch, not by tool name. A targeted unit, API, CLI, or browser test can be right. Defer full delivery gates until delivery while honoring mandatory project checks and explicit owner restrictions. If a required path conflicts with those restrictions, preserve the work and report the conflict without bypassing the hook or running the forbidden check. Name any remaining check gap.

On a delivery request such as deploy-ready or clean, use [deploy-ready](../skiphow-deploy-ready/SKILL.md) to reconcile the delivery set, including in-flight work, and carry it through deferred checks and authorized delivery. Production still needs its applicable explicit grant. On pause or resume, keep and reconcile accepted work, the shown state, pending feedback, resources, and remaining checks through tracked work. Handle new messages when the host delivers them, and do not claim background execution or automatic resumption the host does not provide.
