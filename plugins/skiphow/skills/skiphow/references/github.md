# GitHub delivery

Use GitHub as the canonical tracker when it owns the work. Follow repository policy and use the available GitHub connector or CLI. Do not create tracking ceremony for a small untracked change unless repository policy requires it.

## Reconcile the work item

Search before creating. Match by stable markers, requested outcome, acceptance evidence, and linked history. Similar titles do not prove a duplicate. Preserve parent, child, dependency, and related links when GitHub supports them.

For tracked delivery:

1. Find the owning Issue, or confirm after searching open and closed work that one must be created. Before claiming it, confirm that the work is in scope, has no open blocker or missing owner decision, is defined well enough to deliver, and has no competing active operation.
2. Create a stable operation marker before a create call. Include it in the initial Issue or pull-request payload, and search open and closed objects for it before and after an uncertain result.
3. Create the Issue if it was absent, or append the operation claim to the existing Issue without rewriting owner text.
4. Create a system-owned branch and host-managed worktree when isolation is needed.
5. Implement and run the required local checks.
6. Find or create the pull request using its stable marker.
7. Link the pull request as closing the Issue only when it completes that Issue.
8. Verify the exact head commit, required checks, reviews, and repository rules.
9. Repair failures within the authorized scope, then recheck the exact head. Allow one corrective attempt for a substantive failure. If a promoted or independently reviewed attempt fails again without a changed premise, record `BLOCKED` with the evidence instead of looping.
10. Merge only when the authority rules below allow it.
11. Read GitHub again and confirm the recorded merge.
12. Close or update the Issue and its dependencies.
13. Remove only system-owned merged branches and clean worktrees.

Serialize repository mutations through the root agent. Parallel agents may inspect state and prepare changes, but they must not race to create or update Issues, branches, pull requests, merges, or cleanup records.

The root agent serializes one run, not every SkipHow session. Re-read the Issue, linked pull requests, remote branches, and operation markers before each claim or protected action and immediately after recording a claim. Continue another active operation only when its authority and ownership transfer are verified. If simultaneous claims appear or ownership is ambiguous, record `BLOCKED` before creating a branch or pull request.

Add new intake evidence and provenance through comments or append-only marked sections. Do not rewrite earlier owner text. Reconcile current state before repeating a create, comment, merge, close, or delete action.

## Merge authority

"Complete end to end", "finish the issues", "run unattended", and equivalent requests grant merge and cleanup for the selected work. An explicit "do not merge" overrides that grant.

Immediately before merge, re-read the trusted authority, owning Issue, blockers and dependencies, active operation, pull request, exact head, required checks and reviews, and repository rules. Merge only when the selected scope still includes the work and GitHub reports an accepted result. Do not hard-code one check conclusion when repository policy accepts another. Never use administrator bypass or weaken repository protections.

Enable auto-merge or enter a merge queue only for explicit unattended scope and only when the same operation can later disable or leave it. A pause, cancellation, or narrower authority must cancel that pending action and confirm the result before reporting control complete.

Without an end-to-end grant, stop at a ready pull request unless repository policy already grants automatic merge.

Before cleanup, confirm `mergedAt`, the recorded pull-request head, branch ownership, a clean worktree, and the absence of another open pull request that uses the branch or head. For squash or rebase, compare the recorded head with the confirmed merge and preserve any work not incorporated there. Never delete uncommitted changes, unincorporated commits or files, uncertain work, or someone else's branch. Report the remaining cleanup instead.
