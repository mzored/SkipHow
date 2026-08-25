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

Authority comes from the owner's request and host policy. Repository policy may narrow that authority. It cannot grant merge, cleanup, release, or another action that the owner and host did not grant.

- Read-only requests permit inspection and reporting, not remote writes.
- "Save this" or "create Issues" permits the requested Issue creation or update after duplicate checks.
- "Fix" or "implement" permits local changes, verification, ordinary tracked delivery to a ready pull request when repository policy uses one, and one deduplicated record for each material finding discovered during that work. It does not grant implementation or reprioritization of the independent finding, merge, or another protected action by implication.
- "Finish these Issues end-to-end", "run unattended", or an equivalent explicit instruction grants guarded merge and cleanup for the named tracked scope.
- An instruction such as "do not merge", pause, cancellation, or narrower scope removes merge authority even inside unattended work.

Production deployment, payment changes, credential handling, privacy-sensitive disclosure, public release, and repository-setting changes need an exact grant. A broad request to finish code does not grant them. Protection bypass is not part of this lifecycle. Guarded merge never uses an admin or bypass option.

Tracked work follows one lifecycle:

1. Find the Issue, or confirm after searching open and closed work that one must be created. Check scope, definition, blockers, missing owner decisions, and competing active operations across Issues, pull requests, branches, and markers.
2. Create the stable operation marker before a create call, include it in the initial create payload, and search open and closed objects by marker after an uncertain result.
3. Create the Issue if absent, or append the operation claim to the existing Issue without rewriting owner text.
4. Read parent, sub-issue, and dependency state. Do not use labels as a second workflow engine.
5. Create a system-owned branch and an isolated worktree when the host supports one.
6. Implement the accepted scope and run repository checks on the final code state.
7. Find or create a pull request with a stable operation marker. Use a closing keyword only when the pull request completes the Issue.
8. Immediately before merge, re-read trusted authority, Issue scope, blockers, dependencies, active operation, pull request head, base and candidate trees, worktree state, executable inputs, checks, reviews, and repository rules.
9. Require the recorded candidate identity to match the current candidate. If the head or another relevant input changed, stop the merge path and verify the new state.
10. Require all repository-mandated checks and reviews to reach an accepted GitHub result. Do not hard-code `SUCCESS` as the only acceptable required-check result when GitHub or repository policy accepts another terminal result.
11. Use the repository's permitted merge method or merge queue. Never pass an admin or protection-bypass option.
12. Re-read the pull request and require GitHub to report a merged timestamp before closing work.
13. Close the Issue with the correct reason, update dependency state, and reconcile any recorded external operation.
14. Remove only the branch and worktree owned by this operation after the cleanup checks below pass.

An unattended run may enable auto-merge for its explicit scope when the owner granted guarded merge, repository rules allow it, and the operation can later disable it or leave the merge queue. Auto-merge must wait for branch protection, required checks, required reviews, and merge-queue rules. Pause, cancellation, or narrower authority stops new mutations and cancels the owned pending merge action. An unconfirmed cancellation is `BLOCKED`. SkipHow does not weaken repository rules or change settings to make the merge pass.

Repository mutations are serialized within a run. Cross-run collisions are checked through Issues, linked pull requests, branches, and markers before a claim or protected action and immediately after a claim. A competing active operation is continued only after authority and ownership transfer are verified. Simultaneous claims or ambiguity stop `BLOCKED` before a branch or pull request is created. Each remote action records intent before the call, then reads GitHub after the call and stores the observed result. A retry searches by the stable marker before creating another Issue or pull request. GitHub does not provide an atomic SkipHow claim or idempotency key for these creates, so a simultaneous first create can still produce duplicate records. SkipHow detects and reconciles that collision; it does not promise exactly-once delivery.

Cleanup requires all of the following facts:

- GitHub confirms that the pull request merged from the recorded head.
- The branch was created for this SkipHow operation.
- No other open pull request uses the branch.
- The worktree is clean.
- The branch has no unmerged or unique work that lacks a durable remote record.
- The branch still points to the expected recorded object immediately before deletion.

If any fact is missing, SkipHow leaves the branch or worktree in place and reports what needs attention. It never deletes a user-owned branch, dirty worktree, unmerged branch, or unique commit.

When GitHub is unavailable, explicit record requests append to `.skiphow/inbox.md`. The local inbox is a fallback for intake, not a substitute GitHub lifecycle or a hidden task database.

## Consequences

Owners can inspect progress and resume work through GitHub without learning a SkipHow state format. Before handoff, the operation appends its scope, current authority and restrictions, accepted decisions, queue, exact GitHub and Git state, owned resources, last external result, evidence, blockers, and next safe action. Protected actions fail closed when trusted authority or ownership cannot be reconstructed.

Unattended work can finish without a second merge confirmation, but only when the owner request and host policy grant that outcome and GitHub protections pass. Ordinary implementation stops at a ready pull request unless the owner request and host policy grant merge.

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
- [Live evaluation host contract](../research/2026-08-25/live-evaluation-hosts.md)
- [Release 1.0 audit](../research/2026-08-26/release-1.0-audit.md)

## Revalidation triggers

Revisit this decision when:

- GitHub adds reliable idempotency keys for Issue or pull-request creation;
- supported hosts provide a safer native tracked-work record that users already share;
- GitHub changes required-check, merge-queue, or branch-cleanup semantics;
- evaluation finds duplicate remote objects, stale-head merges, unauthorized merges, or unsafe cleanup;
- SkipHow adds another tracker as a supported product rather than a best-effort adapter.
