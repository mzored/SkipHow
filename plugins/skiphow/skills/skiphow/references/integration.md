# Integration

Open this when the work is done but not where it belongs: a branch or isolated checkout waiting to be integrated and cleared away, a merge or rebase or cherry-pick or revert stopped on a conflict, or a shared destination the request named. Work that stays in the checkout it started in, with no destination named, has nothing here to land.

Landing work is two things, and the second is the one that gets dropped: carrying the change to where this project calls it integrated, then clearing away what the work created. A verified change sitting on a branch nobody merged is not a finished request, and an integrated change whose branch and checkout are still lying around is finished work that left litter behind.

## Where the work lands

Read the integration path and the target branch off the project's own recent history, rather than asking for them or inventing a path of your own. That history settles the path and never the grant: reaching a shared branch or a review is shared delivery, which happens only where the owner's own request names that destination. Where that history merges work straight into an integration branch, do that; where work lands through review instead, the change reaches that review in the state it should be reviewed in, and this branch is finished there. Merging past a gate the project keeps is not finishing faster, and a failed guard is never bypassed to manufacture delivery.

Where the request or the repository's workflow puts this work in a tracker, [tracked work](tracked-work.md) governs when that item closes and what goes into it. Where it could not be integrated at all, say what blocks it and leave the branch alone.

## Verifying the integrated state

Verify against the integrated state, not the branch. The merged result is a state neither side ran its checks on, so an earlier pass on the branch alone does not carry. If the merged result fails, leave everything in place and diagnose it there; nothing is gained by unwinding a merge you are about to redo.

## When it conflicts

Where the request does not authorize changing the conflicted work, inspect and report without modifying the active operation.

Recover what each side was trying to do before choosing between them, from the active operation, the conflicting files, nearby history, commit messages and tests. Do not treat conflict markers as enough context; they show what differs, never why.

Resolve each hunk so the combined result preserves both intents where they are compatible. Where they genuinely oppose each other, choose the behavior matching the stated integration goal and the current product contract, without inventing unrelated behavior while reconciling code. A resolution that silently drops the other side's change is a defect, not a resolution, however cleanly it makes the conflict disappear. Say afterwards which intent could not be preserved, and the evidence behind the choice.

Do not abort, skip, or discard commits where that could lose unique or foreign work, without the exact grant the kernel requires. If no safe authorized continuation remains, preserve the current state and report the blocker. Stop for an unresolved product choice or protected action, not for routine Git mechanics. Otherwise run the relevant checks on the resolved state, inspect the resulting diff, and carry the operation through to completion.

## Clearing away what the work created

Order matters: removing before arrival is established is how work is lost.

1. Establish that the change itself arrived where the project calls it integrated. A squashed or rebased merge leaves no commit in common, so a missing shared commit is not evidence that work is unmerged; look for the change, not for the original commits.
2. Confirm nothing still holds it. An open review means the work is not integrated yet, and its branch and checkout are still in use.
3. Remove only what your own work created; a workspace the host itself owns is cleaned up by the host.

A refusal to remove a branch or a checkout is a question to answer, never an obstacle to force past on the way to a tidy result. Read what it is actually about: commits whose change arrived nowhere, files that were never committed, a lock, a checkout still in use. One that merely reflects a merge which rewrote the work tells you nothing new once arrival is established, and removal may proceed. One that reflects work existing only there stops you — show what is at stake and settle it rather than discarding it. Deleting unintegrated work, rewriting shared history, or removing a ref you do not own needs the exact grant the kernel requires for material deletion.

### Retiring what earlier runs left

The run that creates a branch usually cannot retire it, because review finishes after the run does. So when you are next doing branch work in a project whose request already authorizes changing it, retire the branches and isolated checkouts your own earlier runs left there, under the same test above. This is working state finished late, and it gains no authority of its own: under a read-only request, or where the project's conventions keep integrated branches, say what is there and leave it. It is bounded to what your own work created, and it is not a licence to sweep the repository or to tidy anything a person is still using.
