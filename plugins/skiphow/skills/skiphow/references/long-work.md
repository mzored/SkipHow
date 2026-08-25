# Long work

Use host-native long-running features when work covers several tracked items, waits on external state, runs unattended, or must survive a session interruption. A large diff alone does not require long-running mode.

## Coordinate through the host

Use the host's goal, background task, resume, subagent, and worktree capabilities. Do not build or invoke a SkipHow runner, daemon, scheduler, provider bridge, or task database.

Keep one root agent responsible for the original outcome, authority, queue, integration, and final evidence. Delegate bounded independent work. Parallelize read-only research freely when useful. Parallelize edits only after the host confirms that it can manage separate worktrees with disjoint ownership. Otherwise keep one writer and serialize every mutation.

GitHub Issues, pull requests, and Git are the source of truth for tracked delivery. At each work-item boundary, update durable external state with the result, evidence, findings, blocker, and next step. Resume from that state after compaction or restart instead of relying on the full transcript.

## Control and failure

Map status, pause, resume, and cancellation requests to the current host task. Preserve completed work and external records when pausing or cancelling. Do not claim a background task, resume guarantee, or cancellation that the host did not confirm.

If the host lacks a needed capability, finish safe bounded work in the current session. Save a handoff in the owning Issue or `.skiphow/handoff.md` with the outcome, authority, current state, evidence, blockers, and next action. Mark unattended continuation or restart recovery `UNVERIFIED`.
