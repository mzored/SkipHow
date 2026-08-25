# Operations

Ordinary work runs in the active host session and needs no SkipHow service. Durable execution is reserved for work that must survive session loss, coordinate independent tracked lanes, or wait and retry without keeping a model active.

## Runner contract

A durable campaign uses the local runner store and a foreground supervisor. `skiphow execute` supervises until the run settles or reaches an invocation limit. `skiphow worker` processes one ready frontier. Detached supervision and reboot integration remain later work.

Controller state uses revision-checked durable records. Provider sessions remain authoritative for transcripts, and GitHub remains authoritative for its remote objects. Recovery records preserve the original request, authority, status, budget basis, task graph, findings, provider session references, checkpoints, and next action. Git and integration identities appear when the caller records them. Material transitions go to a hash-linked append-only journal. The store redacts recognized secret forms before persistence.

Startup runs SQLite quick and foreign-key checks, then verifies every event hash chain. It cross-checks journaled task, finding, checkpoint, route, attempt, and security-audit identities against their materialized rows. If those records are missing, malformed, or disagree with their indexed columns, the store may repair them from one of the three newest snapshots, but only when the snapshot hash is valid and its event sequence and journal hash match the exact current head. The store assembles each snapshot and its recovery rows inside one SQLite transaction, so concurrent writers cannot produce a mixed image. Journal damage stops startup. A snapshot cannot replace or rewrite the journal.

Opening a schema 1 database creates a consistent sibling backup with SQLite's Online Backup API before applying schema 2 in one transaction. A failed migration leaves the source at schema 1 and keeps the backup. Restore by stopping runner processes and replacing the database with that backup. Do not copy the live database file while WAL mode is active, and do not place the authoritative database on a network or cloud-synchronized filesystem.

Run states are `NEW`, `READY`, `RUNNING`, `WAITING_EXTERNAL`, `PAUSED`, `VERIFYING`, `COMPLETED`, `BLOCKED`, `FAILED`, and `CANCELLED`. Task states also cover claims, circuit breaking, and supersession. Transitions are monotonic. A stale worker cannot move newer or terminal state backward.

Each claimed attempt has an idempotency key, worker, lease, progress record, failure signature, and next action. It can also record owned paths, base and head identities, and a provider session. The supervisor renews the lease while awaiting provider events. Expired claims return to the ready frontier, including a verifier recovery step when needed.

External waits are explicit. The runner releases the model while waiting and rechecks on a bound schedule. Repeated failures with the same signature trigger a circuit breaker instead of an infinite retry loop.

Provider routes are durable. The runner stores the sticky lane route and every attempt outcome, including exact provider and model version, usage, cost, latency, verification, retries, promotion, and terminal result. Later invocations rebuild calibration from this history. A failed verifier can promote at a checkpoint; it cannot switch a lane during an unfinished reasoning chain.

When reported context health approaches the provider limit, the supervisor saves completed evidence and the next action before requesting compaction. Codex uses App Server compaction. Claude uses Agent SDK compact hooks when the SDK is available; the structured CLI is the fallback. If compaction is unsupported or fails, the task returns to the frontier with a forced-new-session recovery capsule.

## Control commands

`status` reports the outcome, run and task states, the current task, completed task outcomes, saved finding count, configured budget record, next action, and required owner action for a blocked run. The `execute` and `worker` receipts add elapsed time, measured provider cost when available, and the invocation exit reason.

`pause`, `resume`, and `cancel` checkpoint the operator request before changing run state. An active supervisor observes pause or cancel, requests provider interruption, and stops dispatch. `resume` reopens scheduling; the next supervisor invocation releases expired leases and due external waits, then tries the recorded provider session before starting a recovery session. These commands do not reconcile GitHub or clean branches and worktrees. Use the integration-specific reconciliation and cleanup path for those resources.

## Foreground execution

Create a run, then supervise it with the returned identifier:

```sh
skiphow start "Finish the ready backlog" --task "Implement the first deliverable"
skiphow execute RUN_ID --provider codex --max-duration 1800 --max-cost 10 \
  --verification-plan .skiphow/verification.json
```

Write-capable execution requires a trusted verification plan. A provider's terminal
event never marks a mutation task `DONE` by itself. The supervisor snapshots declared
forbidden paths before dispatch, then checks the final filesystem, evidence files, and
bounded commands after the provider stops. A missing task entry or an entry with no
checks fails closed. Programmatic callers may inject a verifier explicitly for tests or
a product-specific integration.

The plan uses task IDs as keys:

```json
{
  "schema_version": 1,
  "tasks": {
    "implement-report": {
      "expected_filesystem": [
        {"path": "src/report.py", "kind": "file", "contains": "def build_report"}
      ],
      "forbidden_mutations": ["pyproject.toml"],
      "commands": [
        {
          "argv": ["python", "scripts/check.py", "--pytest", "tests/test_report.py", "-q"],
          "trusted_artifacts": ["scripts/check.py", "tests/test_report.py"],
          "timeout_seconds": 120,
          "exit_code": 0
        }
      ],
      "evidence": ["test-results/report.json"]
    }
  }
}
```

Use `"*"` instead of a task ID to supply a default contract. An exact task entry takes
precedence over the default.

Paths must be relative to the project and cannot traverse symlinks outside it. Every
command requires a non-empty `trusted_artifacts` list. It must name every project-local
script, test, fixture, and configuration file whose contents determine that command's
verdict. The supervisor fingerprints those artifacts and the resolved executable before
provider dispatch. If either changes, verification refuses to run the command.

The executable is resolved once during that trusted preparation step and invoked by its
recorded absolute path. A provider cannot substitute another executable by changing
`PATH` after dispatch. The verifier does not trust a test or verification script merely
because the provider created or modified it; such a change fails its pre-dispatch
fingerprint. Commands run without a shell or stdin, inherit only a small allowlist of
process environment variables, have a 300 second maximum timeout, and keep at most 64
KiB from each output stream. The plan is trusted executable configuration because its
command arrays can run local programs. Its author is responsible for listing the full
project-local verifier supply chain in `trusted_artifacts`.
Verification results and evidence references are stored in the `after_verification`
checkpoint. Security decisions, session boundaries, and final outcomes also enter a
redacted hash-linked audit chain through compare-and-swap writes.

`--max-duration` and `--max-cost` apply to one foreground invocation. Reported cost is restored from prior process-exit checkpoints. If a provider does not report cost, the receipt marks the cost ceiling as unenforced. Duration and cost stops are checkpointed. They are not lifetime billing guarantees.

## Current implementation status

The optional Python package implements the transactional store, task frontier, leases, checkpoints, recovery capsules, findings, circuit breaker, provider adapters, foreground supervisor, state-derived reconciliation, and CLI controls. Deterministic tests cover dependency dispatch, session resume and fallback, lease renewal and expiry, external waits, duration and reported-cost stops, redaction, process reopen, and idempotent recovery at the tested local boundary.

Persisted recheck deadlines return due external waits to the ready frontier without holding a model. `skiphow github-deliver` uses the same store for a replay-safe GitHub operation: it binds the plan to saved authority, serializes concurrent invocations, reconciles before mutation, waits on external checks or reviews, and writes a final receipt only after exact remote verification.

The deterministic suite covers schema 1 migration, backup preservation after migration failure, hash-chain rejection, exact-head recovery after a real child-process exit, durable route calibration, security-audit conflicts, context recovery, environment verification, and GitHub delivery crash windows. The substrate spike also verifies a no-model Codex App Server terminate/resume cycle. Authenticated Claude execution, multi-trial real provider and service outcomes, adaptive-routing ablation, and cross-platform operation remain `UNVERIFIED`. Core direct work remains usable without the runner.

The read-only diagnostic command is:

```sh
python plugins/skiphow/scripts/doctor.py
```

Doctor reports availability and package proof separately. `UNVERIFIED` means proof is missing, not that a check passed. Uninstalling the plugin does not remove `.skiphow` data, branches, Issues, comments, Projects, or campaign records. Remove those separately only after checking ownership and retention needs.
