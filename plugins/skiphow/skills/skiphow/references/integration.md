# Integration

Open this when work is done but not yet where it belongs: a branch or worktree to integrate or clear away, a merge, rebase, cherry-pick, or revert stopped on a conflict, a delivery, CI, or a release, or leftovers from earlier sessions.

Work is unfinished while the authorized result names a destination it has not reached. A named pull request, integration branch, release, or deployment is done only when you have verified it there. A local branch or worktree used only as working space creates no delivery obligation, and a local change with no shared destination is complete in its local state. Landing work has two parts, and the second is the one that gets dropped: carrying the change to its destination, then clearing away what this run created and what earlier sessions left integrated.

## Lanes and working state

A session or delegate lane is live while its changes still move, its review is open, its tracker record is live, or the host lists it. A branch name, a timestamp, or a running process alone proves nothing either way. Never overwrite, reset, publish, delete, or absorb a live lane.

Keep working state in the project, in the host's working area, or in an ignored location. A worktree goes inside the project in an ignored directory, created and ignored if absent, unless the host manages its own.

Bound work in progress by what you can integrate and review. Lanes you cannot verify are hidden inventory, not speed. Finish and integrate one slice before opening another on the same boundary.

## Where the work lands

Take the destination from the owner's request and any standing grant that applies. Read the integration path and target branch from trusted project procedure and recent history; they explain the path but grant nothing. Carry routine push, pull request, and merge through only the project's established non-production workflow, verified for this project, destination, audience, and effect; then it needs no renewed approval. If the target is a review, deliver a reviewable change there. If it is integration after review, continue through the required review and merge. A failed guard or a required human gate stays part of that boundary.

Choose delivery units from the accepted results by dependency, rollback needs, and project procedure. A delivery grant settles what may travel, not how often, so batch work already held where review and procedure allow instead of publishing each finished assignment. Keep an independent finished result moving when unrelated work is blocked.

While the owner is iterating, nothing travels. Within implementation or iteration, combine accepted results locally when checking them together helps; a lead's intermediate branch is working state, not the destination, unless the request makes it one. Local combination grants no shared delivery and no right to publish an experiment. Wait when nothing can advance safely or the owner asks you to. When a change could be read as either iteration or delivery, show it and say what delivery would add.

Before using the path, look at what it does downstream now. CI or branch rules may have changed, and a merge or tag may now publish a release or deploy production. Know which action changes production and what rollback means for this product. Apply the kernel's protected-action rule to those effects. When the grant does not cover them, finish the authorized preparation and checks, then report the exact remaining action and the grant it needs.

Where the request or the project puts this work in a tracker, [tracked work](tracked-work.md) decides when the item closes. Where the work cannot be integrated at all, say what blocks it and leave the branch alone.

## Verifying the integrated state

Check the integrated candidate, including revision-bound CI, unless a passing check already ran on the same tree, command, and environment; then reuse it. A check on a different tree proves nothing about this one. A stage name such as integration or release requires no repeat. Promote one immutable candidate through later stages and reuse its checks while their inputs are equal; add an environment-specific check only for a property earlier checks could not show.

Inspect the destination separately, because passing checks do not show that delivery happened. A rehearsal, a package validator, or a preview is not proof that users received the change.

If the merged result fails, keep its evidence and any unrelated work first, then choose the recovery by consequence. A failing local merge or disposable branch can stay in place for diagnosis. A failing shared target that other work, CI, or a deployment depends on is contained or restored to its last good state while diagnosis continues, whenever that is safer than leaving it broken. A revert on a covered non-production destination needs no new approval; restoring production still needs the production grant. Never report the failed state as delivered.

## Keeping the project releasable

Local setup, CI, release paths, and recovery procedures are engineering assets. Repair one when it blocks or repeatedly taxes the requested result, and build no process infrastructure for maturity's sake. Use the CI provider's native features, such as caching, matrices, path filters, and required checks, before writing custom scripts.

Answer local questions with the shortest feedback loop that still represents the behavior, and run the slow comprehensive check near integration. For slow or flaky suites, see [testing](testing.md).

## When it conflicts

Where the request does not authorize changing the conflicted work, inspect and report without touching the active operation.

Recover what each side was trying to do before choosing between them, from the operation in progress, the conflicting files, nearby history, commit messages, and tests. Conflict markers show what differs, never why.

Resolve each hunk so the result keeps both intents where they are compatible. Where they truly oppose each other, choose the behavior that matches the integration goal and the current product, without inventing new behavior along the way. A resolution that silently drops the other side's change is a defect, however cleanly the conflict disappears. Say afterwards which intent you could not keep and why.

Do not abort, skip, or discard commits where that would lose a live lane's changes or anything Git cannot recover; that loss needs the grant the kernel requires. A recoverable commit from this run or an earlier session is yours to keep or drop by the integration goal, and the report names each dropped commit and its hash. Stop for an open product choice or a protected action, not for routine Git mechanics. If no safe authorized way forward remains, keep the current state and report the blocker. Otherwise check the resolved state, read the resulting diff, and finish the operation.

## Clearing away what the work created

Order matters, because removing before arrival is established is how work is lost.

1. Establish that the change arrived where the project calls it integrated. A squash or rebase merge leaves no shared commit, so look for the change itself, not the original commits.
2. Confirm nothing still holds it. An open review means the work is not integrated, and its branch and checkout are still in use.
3. Under a change request, remove what this run created and what earlier sessions left once it is integrated and nothing holds it, including scratch plans and reports. The host cleans up workspaces it owns. A worktree with uncommitted changes stays.

Settle each finished session's leftover and say how. A refusal to remove a branch or checkout is a question to answer, never an obstacle to force. Read what it is about: commits whose change arrived nowhere, uncommitted files, a lock, or a checkout in use. One that only reflects a merge that rewrote the work tells you nothing new once arrival is established, and removal may proceed. One that reflects work that exists only there is your decision. Where the current product shows the attempt superseded or abandoned, retire it and report the commit it held and how to recover it. Otherwise finish and integrate it under the kernel's rule for findings, or defer it with the reason, and say which. Uncommitted files, history others share, and anything unrecoverable keep the grant the kernel requires for material deletion.

Under a read-only request, report each leftover with the disposition you would take and retire nothing; the next change request carries it out. Where trusted project procedure keeps integrated branches, keep them and say so.
