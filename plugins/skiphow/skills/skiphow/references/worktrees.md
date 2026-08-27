# Worktrees and integration

Load this reference before mutation when another writer may touch the checkout, when the host offers isolation, or when the checkout, branch, or `HEAD` no longer matches the state the run inspected. Isolation is normal engineering work and needs no owner confirmation.

## Establish ownership

Read repository instructions first. Record the repository root, common Git directory, worktree path, branch, `HEAD`, status, intended base, and observable active host tasks. An unavailable host task inventory is unknown, never proof that no writer exists; use fresh exclusive isolation. Detect an existing linked worktree before creating one; a submodule is not proof of worktree isolation. Prefer the host's native worktree mechanism because the host owns its placement, lifecycle, and safety checks. Otherwise create a linked Git worktree in the repository's established ignored location after proving it ignored. If none exists, use an operation-specific directory under the operating system's temporary area, outside the checkout; do not change `.gitignore` merely to create isolation.

One writing lane owns one worktree and one branch. Never write in a shared checkout while another task may write there, and never let two lanes share a branch. Record whether a host-native worktree is branched or detached. Before the first deliverable commit, create a named owned ref through the host or Git's ordinary branch command; if the host owns detached lifecycle, anchor the returned commit to an owned ref before cleanup. A fresh worktree may start from the default branch rather than the sender's current state, so verify the exact base and every prerequisite before the first write.

## Guard against drift

Immediately before a mutation, commit, review, gate, or integration, compare the live worktree, branch, `HEAD`, status, and active tasks with the recorded identity. If they drift, stop writes in that checkout. Do not commit while ownership is uncertain. Identify and preserve only the proven owned tracked delta and owned untracked files, establish a new isolated worktree at the intended base, apply only that material, and commit there after attribution and exclusive ownership are restored. Rerun invalidated checks.

Do not repair identity by overwriting files from the index, redirecting Git through an alternate index or worktree, creating commits with plumbing commands, moving refs directly, force-checking out paths, bypassing hooks, or resetting foreign work. Never override a branch-in-use or dirty-worktree refusal with `git worktree add --force` or `git worktree remove --force`; the refusal is ownership evidence. Those actions hide the candidate that was actually reviewed and can destroy another lane's changes.

## Integrate every finished unit

The builder commits its owned change with the repository's ordinary commit path and hooks. The root verifies the returned commit and diff against the recorded base, then integrates it into the root operation branch. Resolve conflicts as integration work under [engineering methods](engineering.md) and run checks for both intents. After every unit is integrated and the target head is current, run fresh affected checks and independent review on the exact aggregate tree; clean integration, target movement, conflict resolution, or any later change invalidates earlier aggregate evidence.

A unit remains in progress until its commit is integrated. Before deleting any source ref or worktree, prove from the durable integration record that no source content is absent from the result; read [GitHub](github.md) for squash and rebase evidence. Record whether the worktree lifecycle belongs to the host or this operation and whether it is the current session directory. For a host-managed or current worktree, safely hand off or exit before the final response only when candidate identity and reporting context survive; otherwise leave cleanup to the host lifecycle and report it pending, never completed. Use Git removal only for a verified-clean, operation-created, non-current worktree, without force, then delete its local branch. Remove only resources owned by the operation.
