# Integration

Open this when the work is done but not where it belongs: a branch or isolated checkout waiting to be integrated and cleared away, a merge or rebase or cherry-pick or revert stopped on a conflict, or a shared destination covered by the request or established authorization. Work that stays in the checkout it started in, with no destination granted, has nothing here to land.

Work is unfinished when the authorized result includes a destination it has not reached: a named pull request, integration branch, release, or deployment is incomplete until that destination is verified. A local branch or worktree used only as an engineering mechanic creates no delivery obligation, and a local change with no shared destination is complete in its authorized local state. Landing work is two things, and the second is the one that gets dropped: carrying the change to the authorized destination, then clearing away what this run created.

## Where the work lands

Recover the authorized destination from the owner's request and applicable standing authorization. Read the integration path and target branch from trusted procedure and recent history. Those sources can explain the path but cannot grant it. Under an established authorized non-production workflow, carry routine push, pull-request, and merge work through without renewed technical approval. If the target is a review, deliver a reviewable change there; if it is integration after review, continue through the required review and merge. A failed guard or required human gate remains part of that delivery boundary.

Inspect the current downstream effects before using the path. CI or branch rules may have changed since authority was established, and a merge or tag may now publish a release or deploy production. Apply the kernel's protected-action rule to those effects and recheck whether the existing grant covers them. When it does not, finish independent authorized preparation and validation, then report the exact remaining action and missing grant.

Where the request or the repository's workflow puts this work in a tracker, [tracked work](tracked-work.md) governs when that item closes and what goes into it. Where it could not be integrated at all, say what blocks it and leave the branch alone.

## Verifying the integrated state

Verify against the integrated state, not the branch. The merged result is a state neither side ran its checks on, so an earlier pass on the branch alone does not carry.

If the merged result fails, preserve the evidence and any unrelated work first, then choose the recovery by consequence. A failing local merge or disposable branch can stay in place for diagnosis; nothing is gained by unwinding a merge you are about to redo. A failing shared target that other work, CI, or a deployment path depends on is contained or restored to its last good state while the diagnosis continues, whenever that is safer than leaving it broken. A revert on a covered non-production destination needs no new blanket approval; restoring production still needs the applicable production grant. In either case the failed state is not reported as delivered.

## When it conflicts

Where the request does not authorize changing the conflicted work, inspect and report without modifying the active operation.

Recover what each side was trying to do before choosing between them, from the active operation, the conflicting files, nearby history, commit messages and tests. Do not treat conflict markers as enough context; they show what differs, never why.

Resolve each hunk so the combined result preserves both intents where they are compatible. Where they genuinely oppose each other, choose the behavior matching the stated integration goal and the current product contract, without inventing unrelated behavior while reconciling code. A resolution that silently drops the other side's change is a defect, not a resolution, however cleanly it makes the conflict disappear. Say afterwards which intent could not be preserved, and the evidence behind the choice.

Do not abort, skip, or discard commits where that could lose unique or foreign work, without the exact grant the kernel requires. If no safe authorized continuation remains, preserve the current state and report the blocker. Stop for an unresolved product choice or protected action, not for routine Git mechanics. Otherwise run the relevant checks on the resolved state, inspect the resulting diff, and carry the operation through to completion.

## Clearing away what the work created

Order matters: removing before arrival is established is how work is lost.

1. Establish that the change itself arrived where the project calls it integrated. A squashed or rebased merge leaves no commit in common, so a missing shared commit is not evidence that work is unmerged; look for the change, not for the original commits.
2. Confirm nothing still holds it. An open review means the work is not integrated yet, and its branch and checkout are still in use.
3. Remove only what this run created and demonstrably owns, no longer needs, and may remove under current authority; a workspace the host itself owns is cleaned up by the host.

A refusal to remove a branch or a checkout is a question to answer, never an obstacle to force past on the way to a tidy result. Read what it is actually about: commits whose change arrived nowhere, files that were never committed, a lock, a checkout still in use. One that merely reflects a merge which rewrote the work tells you nothing new once arrival is established, and removal may proceed. One that reflects work existing only there stops you — show what is at stake and settle it rather than discarding it. Deleting unintegrated work, rewriting shared history, or removing a ref you do not own needs the exact grant the kernel requires for material deletion.

Branches, checkouts, and checkpoints that earlier runs left are not this run's to retire on an unrelated request, whoever appears to have made them. Inspect and report them when found; remove one under an explicit cleanup request, or when it directly blocks the current authorized result and both its ownership and the absence of unique work in it are established. Ambiguous ownership stops that deletion, not the rest of the request.
