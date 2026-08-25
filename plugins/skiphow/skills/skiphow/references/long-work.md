# Long work

Use host-native long-running features when work covers several tracked items, waits on external state, runs unattended, or must survive a session interruption. A large diff alone does not require long-running mode.

## Coordinate through the host

Use the host's goal, background task, resume, subagent, and worktree capabilities. Do not build or invoke a SkipHow runner, daemon, scheduler, provider bridge, or task database.

Keep one root agent responsible for the original outcome, authority, queue, integration, and final evidence. Delegate bounded independent work. Parallelize read-only research freely when useful. Parallelize edits only after the host confirms that it can manage separate worktrees with disjoint ownership. Otherwise keep one writer and serialize every mutation.

Before unattended work, confirm the selected scope, background and resume capability, repository and tracker access, approval mode, CI visibility, merge rights when granted, and any provider spending limit. Do not promise an overnight outcome that will stop at a known approval or missing capability. Complete a safe subset only when it remains useful and report the reduced guarantee.

GitHub Issues, pull requests, and Git are the source of truth for tracked delivery. At each work-item boundary, and before a known compaction, pause, cancellation, or handoff, append a checkpoint to the owning record. Include a stable task and checkpoint ID, selected scope, current authority and later restrictions, accepted decisions, remaining queue and dependencies, Issue, branch, worktree, pull request and exact head, owned resources, last external action and result, evidence, blockers, and next safe action.

Without a tracker, append the same fields to `.skiphow/handoff.md`. Use a `## <task-id> / <checkpoint-id>` heading and these exact labels: `Recorded`, `Selected scope`, `Authority`, `Later restrictions`, `Accepted decisions`, `Queue and dependencies`, `Issue`, `Branch`, `Worktree`, `Pull request`, `Exact head`, `Owned resources`, `Last external action`, `Last external result`, `Evidence`, `Blockers`, and `Next safe action`. Write one `- <Field>: <value>` line per label, with `Recorded` first in RFC 3339 UTC. Never replace an earlier checkpoint or another task's block. After compaction or restart, re-read the trusted owner request and host task, repository instructions, latest checkpoint, Git, and GitHub before mutating anything. Missing or conflicting scope, authority, ownership, or exact state forbids merge, cleanup, and other protected actions until reconciled.

## Control and failure

Map status, pause, resume, and cancellation requests to the current host task. Pause, cancel, and any narrower authority stop new mutations first. Revoke merge authority, disable owned pending auto-merge, leave an owned merge queue entry when the repository permits it, and then re-read GitHub. Preserve completed work and external records. If a pending action cannot be cancelled or its state cannot be confirmed, report `BLOCKED` instead of claiming the task is paused or cancelled.

If the host lacks a needed capability, finish safe bounded work in the current session. Save the checkpoint above in the owning Issue or `.skiphow/handoff.md`. Mark unattended continuation or restart recovery `UNVERIFIED`.
