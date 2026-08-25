# Operations

Ordinary work runs in the active host session and needs no SkipHow service. Durable execution is reserved for work that must survive session loss, coordinate independent tracked lanes, or wait and retry without keeping a model active.

## Runner contract

A durable campaign uses the local runner store and a foreground supervisor. `skiphow execute` supervises until the run settles or reaches an invocation limit. `skiphow worker` processes one ready frontier. Detached supervision and reboot integration remain later work.

Controller state uses revision-checked durable records. Provider sessions remain authoritative for transcripts, and GitHub remains authoritative for its remote objects. Recovery records preserve the original request, authority, status, budget basis, task graph, findings, provider session references, checkpoints, and next action. Git and integration identities appear when the caller records them. Material transitions also go to an append-only journal. The store redacts recognized secret forms before persistence.

Run states are `NEW`, `READY`, `RUNNING`, `WAITING_EXTERNAL`, `PAUSED`, `VERIFYING`, `COMPLETED`, `BLOCKED`, `FAILED`, and `CANCELLED`. Task states also cover claims, circuit breaking, and supersession. Transitions are monotonic. A stale worker cannot move newer or terminal state backward.

Each claimed attempt has an idempotency key, worker, lease, progress record, failure signature, and next action. It can also record owned paths, base and head identities, and a provider session. The supervisor renews the lease while awaiting provider events. Expired claims return to the ready frontier, including a verifier recovery step when needed.

External waits are explicit. The runner releases the model while waiting and rechecks on a bound schedule. Repeated failures with the same signature trigger a circuit breaker instead of an infinite retry loop.

## Control commands

`status` reports the outcome, run and task states, the current task, completed task outcomes, saved finding count, configured budget record, next action, and required owner action for a blocked run. The `execute` and `worker` receipts add elapsed time, measured provider cost when available, and the invocation exit reason.

`pause`, `resume`, and `cancel` checkpoint the operator request before changing run state. An active supervisor observes pause or cancel, requests provider interruption, and stops dispatch. `resume` reopens scheduling; the next supervisor invocation releases expired leases and due external waits, then tries the recorded provider session before starting a recovery session. These commands do not reconcile GitHub or clean branches and worktrees. Use the integration-specific reconciliation and cleanup path for those resources.

## Foreground execution

Create a run, then supervise it with the returned identifier:

```sh
skiphow start "Finish the ready backlog" --task "Implement the first deliverable"
skiphow execute RUN_ID --provider codex --max-duration 1800 --max-cost 10
```

`--max-duration` and `--max-cost` apply to one foreground invocation. Reported cost is restored from prior process-exit checkpoints. If a provider does not report cost, the receipt marks the cost ceiling as unenforced. Duration and cost stops are checkpointed. They are not lifetime billing guarantees.

## Current implementation status

The optional Python package implements the transactional store, task frontier, leases, checkpoints, recovery capsules, findings, circuit breaker, provider adapters, foreground supervisor, state-derived reconciliation, and CLI controls. Deterministic tests cover dependency dispatch, session resume and fallback, lease renewal and expiry, external waits, duration and reported-cost stops, redaction, process reopen, and idempotent recovery at the tested local boundary.

Persisted recheck deadlines return due external waits to the ready frontier without holding a model. Detached supervision, automatic restart after machine reboot, authenticated Claude execution, and multi-trial live provider recovery remain `UNVERIFIED`. Core direct work remains usable without the runner.

The read-only diagnostic command is:

```sh
python plugins/skiphow/scripts/doctor.py
```

Doctor reports availability and package proof separately. `UNVERIFIED` means proof is missing, not that a check passed. Uninstalling the plugin does not remove `.skiphow` data, branches, Issues, comments, Projects, or campaign records. Remove those separately only after checking ownership and retention needs.
