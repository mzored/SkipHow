# ADR 0004: Use GitHub as the tracked-work record

## Status

Accepted

## Date

2026-08-25

## Context

Owners often collect ideas and bugs first, then ask SkipHow to finish a set of Issues without watching every step. They need one durable record of scope, progress, review, and completion. A second task database drifts from GitHub and forces users to reconcile two versions of the same work.

Small local changes do not need an Issue, branch, and pull request by default. Tracked or unattended work does need stronger rules. Merge and cleanup are remote changes, and a stale head or broad cleanup command can destroy work even when tests were green earlier.

The retired runtime split local execution from GitHub delivery. It could mark a run complete before a pull request, required checks, merge, Issue closure, and branch cleanup had finished. The replacement needs one lifecycle with explicit authority.

## Decision

When a repository uses GitHub and the work is tracked, GitHub is the source of truth. Issues hold the accepted work items and their relationships. Pull requests hold delivery and review state. Git records the exact code state. SkipHow does not maintain a parallel task database.

A small direct task may stay untracked unless the user or repository policy requires an Issue or pull request.

Authority comes from the user's request and repository policy.

- Read-only requests permit inspection and reporting, not remote writes.
- "Save this" or "create Issues" permits the requested Issue creation or update after duplicate checks.
- "Fix" or "implement" permits local changes, verification, and ordinary tracked delivery to a ready pull request when repository policy uses one. It does not grant merge or another protected action by implication.
- "Finish these Issues end-to-end", "run unattended", or an equivalent explicit instruction grants guarded merge and cleanup for the named tracked scope.
- An instruction such as "do not merge" removes merge authority even inside unattended work.

Production deployment, payment changes, credential handling, privacy-sensitive disclosure, public release, and repository-setting changes need an exact grant. A broad request to finish code does not grant them. Protection bypass is not part of this lifecycle. Guarded merge never uses an admin or bypass option.

Tracked work follows one lifecycle:

1. Find or create the Issue with a stable operation marker. Search open and closed Issues before creating a new one.
2. Read parent, sub-issue, and dependency state. Do not use labels as a second workflow engine.
3. Create a system-owned branch and an isolated worktree when the host supports one.
4. Implement the accepted scope and run repository checks on the final code state.
5. Find or create a pull request with a stable operation marker. Use a closing keyword only when the pull request completes the Issue.
6. Record the pull request head commit. Re-read the pull request before every merge attempt.
7. Require the recorded head to match the current head. If it changed, stop the merge path and verify the new state.
8. Require all repository-mandated checks and reviews to reach an accepted GitHub result. Do not hard-code `SUCCESS` as the only acceptable required-check result when GitHub or repository policy accepts another terminal result.
9. Use the repository's permitted merge method or merge queue. Never pass an admin or protection-bypass option.
10. Re-read the pull request and require GitHub to report a merged timestamp before closing work.
11. Close the Issue with the correct reason, update dependency state, and reconcile any recorded external operation.
12. Remove only the branch and worktree owned by this operation after the cleanup checks below pass.

An unattended run enables auto-merge by default only for its explicit scope. Auto-merge must wait for branch protection, required checks, required reviews, and merge-queue rules. SkipHow does not weaken those rules or change repository settings to make the merge pass.

Repository mutations are serialized. Each remote action records intent before the call, then reads GitHub after the call and stores the observed result. A retry searches by the stable marker before creating another Issue or pull request. SkipHow promises reconciliation, not exactly-once delivery from an API that lacks idempotency keys for these creates.

Cleanup requires all of the following facts:

- GitHub confirms that the pull request merged from the recorded head.
- The branch was created for this SkipHow operation.
- No other open pull request uses the branch.
- The worktree is clean.
- The branch has no unmerged or unique work that lacks a durable remote record.

If any fact is missing, SkipHow leaves the branch or worktree in place and reports what needs attention. It never deletes a user-owned branch, dirty worktree, unmerged branch, or unique commit.

When GitHub is unavailable, explicit record requests append to `.skiphow/inbox.md`. The local inbox is a fallback for intake, not a substitute GitHub lifecycle or a hidden task database.

## Consequences

Owners can inspect progress and resume work through GitHub without learning a SkipHow state format. Compaction and session restart can reconstruct tracked state from Issues, pull requests, checks, and Git.

Unattended work can finish without a second merge confirmation, but only when the initial request grants that outcome and GitHub protections pass. Ordinary implementation stops at a ready pull request unless the repository policy or user grants merge.

Some repositories do not expose native Issue dependencies or merge queues. SkipHow uses the available GitHub state and reports unsupported behavior. It does not recreate those services locally.

## Rejected alternatives

### Keep a SkipHow task database beside GitHub

Two mutable records create reconciliation work and ambiguous ownership. GitHub already stores the tracked objects that collaborators use.

### Require GitHub ceremony for every change

This slows small local fixes and contradicts proportional execution. Repository policy may still require the full lifecycle.

### Merge every successful implementation

A green local check does not grant a remote merge and does not prove that the pull request head, reviews, or protections still match.

### Never merge automatically

This would leave explicit unattended work unfinished even after the owner granted end-to-end delivery and all repository protections passed.

### Use admin merge or change repository settings

Bypassing protections hides a real blocker. Changing settings also affects work outside the requested scope.

### Treat branch deletion as harmless cleanup

A branch can contain unique work or belong to another person. Cleanup needs provenance, exact state, and confirmed merge.

## Evidence

- [Product and UX research](../research/2026-08-25/product-and-ux.md)
- [Host-capability research](../research/2026-08-25/host-capabilities.md)
- [Repository audit](../research/2026-08-25/repository-audit.md)
- [Security and evaluation research](../research/2026-08-25/security-and-evals.md)

## Revalidation triggers

Revisit this decision when:

- GitHub adds reliable idempotency keys for Issue or pull-request creation;
- supported hosts provide a safer native tracked-work record that users already share;
- GitHub changes required-check, merge-queue, or branch-cleanup semantics;
- evaluation finds duplicate remote objects, stale-head merges, unauthorized merges, or unsafe cleanup;
- SkipHow adds another tracker as a supported product rather than a best-effort adapter.
