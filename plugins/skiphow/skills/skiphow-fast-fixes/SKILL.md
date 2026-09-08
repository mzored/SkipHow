---
name: skiphow-fast-fixes
description: Iterate on a local screen or other visible result with the owner before delivery. Use for small copy, layout, and frontend changes shown on a running dev preview, with feedback checkpoints and deferred delivery tests. A request to ship uses the delivery workflow.
---

# SkipHow fast-fixes

Give the owner a working preview to inspect and revise. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. The lead remains the CTO; this session's completion boundary is each reviewed and shown iteration.

Prepare an isolated branch and worktree from the project's current development base. Discover the base, dev startup command, and existing preview conventions rather than assuming branch names or commands. Preserve unrelated changes. Reuse this session's owned workspace on subsequent turns. Keep its preview and worktree available while the iteration session continues, and preserve the minimal outcome-to-workspace association for recovery under [tracked work](../skiphow/references/tracked-work.md).

Make the requested bounded change. Use [verification](../skiphow/references/verification.md) for review, rendered inspection, and permitted focused checks. Show the actual running preview at a usable address or through the host's preview tool, with a concise account of the change, then stop for feedback. If the preview cannot run, report the blocker and do not represent an unshown result as shown.

Defer Playwright/e2e test runs, full backend gates, and pytest until delivery. Browser interaction and screenshots for inspecting the preview remain appropriate. Inspect the effects of project commands and commit hooks so they do not run deferred suites indirectly. If the permitted commit path requires a deferred check, report the conflict and preserve the work; do not bypass the hook or silently run the suite. Name verification gaps when a requested change cannot be checked sufficiently within this boundary.

When feedback or the next task arrives, commit the previous shown iteration as a checkpoint before making further edits, even when the feedback requests a revision. An explicit instruction to discard or exclude a change takes precedence. Commit only this session's owned changes. Feedback and acceptance keep the session in iteration mode and do not trigger push, shared integration, or delivery tests.

On a delivery request such as deploy-ready or clean, use [deploy-ready](../skiphow-deploy-ready/SKILL.md) to carry the accumulated changes through deferred checks and authorized delivery. Deployment to production still needs its applicable explicit grant. On pause or resume, preserve and reconcile the shown state, pending feedback, owned preview resources, and remaining verification through the kernel's continuation rules.
