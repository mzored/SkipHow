# Trust and operations

The detailed abuse cases and residual risks are in the [threat model](threat-model.md).

## What runs

Direct plugin work runs only in the current host session. Durable work can start the optional local `skiphow` runner. `execute` runs a foreground supervisor, and `worker` handles one ready frontier. Neither command installs a daemon, hook, hosted service, telemetry client, or MCP server.

Provider adapters may start an installed Codex App Server or the current structured Claude CLI transport. The Claude adapter protocol can accept another transport, but a production Agent SDK transport is not included. Adapters receive an explicit permission profile and project working directory. Read-only scouts and reviewers do not receive write or remote-mutation authority. A subagent boundary is context isolation, not a security boundary.

## State and files

The default project state is below `.skiphow/runs`. SQLite stores authoritative run and task records, leases, checkpoints, findings, and material audit events. The event journal is append-only. JSON exports and snapshots support inspection; they are not separate authority.

The runner preserves the original request, constraints, evidence saved in checkpoints, provider session IDs, and the next action. It preserves Git identity only when a caller records it. Raw provider transcripts remain with the provider or host and are not copied into recovery capsules.

Project configuration is `.skiphow/config.json`. Personal provider catalogs, model IDs, cost preferences, and budgets live under the user's platform configuration directory. Provider tokens remain in environment variables or provider credential stores. Do not place tokens or API keys in either configuration file.

## Network and remote changes

The core runner needs no network. A provider adapter can contact its configured provider. The GitHub adapter can contact GitHub for authorized Issue, relationship, branch, pull request, check, merge, and cleanup operations. Live evals make provider calls only after explicit opt-in, credentials, and budget.

Repository files, Issue and pull request bodies, web pages, test output, generated files, and worker summaries are untrusted data. They cannot grant authority or override the request, host policy, repository instructions, or protected-action checks.

GitHub helpers reconcile actual state and use operation markers or exact remote identities before their mutations. The generic provider supervisor does not dispatch the GitHub lifecycle. Remote persistence, merge policy, and finding persistence still come from authority and project configuration. A GitHub Project is an optional view, not lifecycle authority.

## Permissions and protected actions

The security module provides resolved filesystem allowlists and rejects symlink traversal outside them. Provider permission modes are passed to the host adapter. GitHub cleanup checks the exact merged pull request, expected branch head, and an owned disposable marker before deletion. These are separate controls, and callers must use the relevant one.

These actions always need explicit authority:

- production deployment or database migration;
- payment or refund;
- credential change;
- privacy data export or deletion;
- irreversible remote deletion;
- public release;
- protected-branch merge when repository policy requires human action.

GitHub tokens should use the least privileges required for the configured lifecycle. Provider sandbox and approval modes remain in force. The runner store redacts recognized token patterns, credential assignments, authorization fields, and private-key blocks before persistence. Unknown secret formats can still escape redaction, so inspect an export before sharing it.

## Pause, cancel, and recovery

Pause, resume, and cancel record an operator checkpoint before changing state. An active supervisor requests provider interruption after it observes pause or cancel. Resume reopens scheduling. The next supervisor invocation releases expired leases and due waits, then tries the recorded provider session before starting a new session from the recovery capsule. Control commands do not delete Git or GitHub resources.

If the process dies, SQLite transactions prevent partial controller transitions. On restart, expired leases return eligible tasks to the ready frontier. Lease fencing and revision checks reject stale worker writes. Attempt identifiers and idempotency keys prevent a completed task transition from being replayed by the store. External adapters still need their own reconciliation identity. Repeated failures with the same signature open a circuit breaker instead of looping forever.

## Diagnostics and evidence

Run `python plugins/skiphow/scripts/doctor.py` for a read-only host and integration report. `AVAILABLE` proves only that a command responded. Package installation, adapter conformance, runtime behavior, and live outcomes require separate receipts. Missing optional proof is `UNVERIFIED`, not a pass.

Deterministic checks run with `python scripts/check.py`. They do not call a model. `python scripts/check.py --offline` never attempts dependency installation and reports missing prepared dependencies as `UNVERIFIED`. Live evals are separate and opt-in.

## Uninstall and data removal

Uninstall the plugin through the host plugin interface and uninstall the `skiphow-runner` Python package through the package manager used to install it. Uninstall does not delete project state or remote records.

After confirming no run is active, remove a specific project's `.skiphow/runs` directory to delete its local run data. Remove `.skiphow/config.json` separately if the project no longer needs configuration. Personal settings live in the configured SkipHow configuration directory. Issues, pull requests, branches, comments, and Projects remain in GitHub until an authorized user removes them.
