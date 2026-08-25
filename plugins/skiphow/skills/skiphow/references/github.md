# GitHub delivery

Use GitHub as the canonical tracker when it owns the work. Follow repository policy and use the available GitHub connector or CLI. Do not create tracking ceremony for a small untracked change unless repository policy requires it.

## Reconcile the work item

Search before creating. Match by stable markers, requested outcome, acceptance evidence, and linked history. Similar titles do not prove a duplicate. Preserve parent, child, dependency, and related links when GitHub supports them.

For tracked delivery:

1. Find or create the owning Issue and record a stable operation marker.
2. Create a system-owned branch and host-managed worktree when isolation is needed.
3. Implement and run the required local checks.
4. Find or create the pull request using its stable marker.
5. Link the pull request as closing the Issue only when it completes that Issue.
6. Verify the exact head commit, required checks, reviews, and repository rules.
7. Repair failures within the authorized scope, then recheck the exact head. Allow one corrective attempt for a substantive failure. If a promoted or independently reviewed attempt fails again without a changed premise, record `BLOCKED` with the evidence instead of looping.
8. Merge only when the authority rules below allow it.
9. Read GitHub again and confirm the recorded merge.
10. Close or update the Issue and its dependencies.
11. Remove only system-owned merged branches and clean worktrees.

Serialize repository mutations through the root agent. Parallel agents may inspect state and prepare changes, but they must not race to create or update Issues, branches, pull requests, merges, or cleanup records.

Before a create operation, record its intent and stable marker in the owning Issue or confirmed host task. Search for that marker before creating and after any interruption. Reconcile current state before repeating a create, comment, merge, close, or delete action.

## Merge authority

"Complete end to end", "finish the issues", "run unattended", and equivalent requests grant merge and cleanup for the selected work. An explicit "do not merge" overrides that grant.

Merge only when the selected scope includes the work, the exact head is unchanged, required checks and reviews pass, branch protection permits it, and the repository permits the chosen merge method. Never use administrator bypass or weaken repository protections.

Without an end-to-end grant, stop at a ready pull request unless repository policy already grants automatic merge.

Before cleanup, confirm `mergedAt`, the recorded pull-request head, branch ownership, a clean worktree, and the absence of another open pull request that uses the branch or head. For squash or rebase, compare the recorded head with the confirmed merge and preserve any work not incorporated there. Never delete uncommitted changes, unincorporated commits or files, uncertain work, or someone else's branch. Report the remaining cleanup instead.
