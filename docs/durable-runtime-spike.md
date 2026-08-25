# Durable runtime spike

Status: decision record, 2026-08-25.

## Decision

Build a bounded embedded controller. Integrate Codex App Server and Claude
Agent SDK or structured CLI as provider adapters. Keep Restate as the fallback
candidate until the same crash test runs against it. Defer Temporal as the
default local runtime.

The controller owns run and task state, leases, external-action receipts,
budgets, deadlines, and terminal reconciliation. Provider sessions remain
foreign records. They own conversation history, not the campaign.

This is a `BUILD` decision for the controller and an `INTEGRATE` decision for
provider sessions. It is narrow on purpose. SkipHow needs a small state machine,
not a general workflow programming system.

## Executable local proof

`scripts/durable_runtime_spike.py` runs one bounded comparison. The embedded
candidate commits a provider-turn receipt, exits in a separate process, resumes
from SQLite, and records the external action once. The provider-native candidate
starts a Codex App Server thread, persists no-model goal metadata, terminates the
server process, resumes the same thread in a new process, and deletes the thread
it created. Restate and Temporal probes fail closed as `UNVERIFIED` when either
the runtime executable or Python SDK is absent.

Run the proof through the repository environment:

```bash
python scripts/check.py --pytest tests/test_durable_runtime_spike.py
```

Run the comparison and write an atomic machine-readable receipt:

```bash
SPIKE_DIR="$(mktemp -d)"
python scripts/durable_runtime_spike.py \
  --compare \
  --workdir "$SPIKE_DIR/state" \
  --output "$SPIKE_DIR/receipt.json"
```

The provider-native step starts no model turn and needs no run budget. It does
require an installed Codex CLI and a writable App Server session store. The
checked local result is
[`durable-runtime-spike-receipt.json`](durable-runtime-spike-receipt.json).

To inspect the two process runs directly:

```bash
SPIKE_DIR="$(mktemp -d)"
python scripts/durable_runtime_spike.py --db "$SPIKE_DIR/runtime.db" --crash-after-provider
python scripts/durable_runtime_spike.py --db "$SPIKE_DIR/runtime.db"
python scripts/durable_runtime_spike.py --db "$SPIKE_DIR/runtime.db"
```

The first process exits with code 75 after its commit. The next process prints
`state=COMPLETED` with one `provider-turn` receipt and one `external-action`
receipt. The third run keeps both counts at one.

Fresh deterministic test result on 2026-08-25:

```text
tests/test_durable_runtime_spike.py ..
2 passed
```

The receipt verifies SQLite process recovery and Codex App Server session
continuity after process termination. It does not turn provider history into
controller state. The runner suite also covers stale lease fencing, revision
conflicts, checkpoints, a process
exit followed by exact-head snapshot repair, and schema 1 to schema 2 migration.
The migration uses SQLite's Online Backup API before an atomic transaction. A
kill during a live provider stream and the uncertainty window of a real GitHub
mutation need their separate outcome receipts.

## Candidate comparison

| Candidate | Local executable result | Recovery and side effects | Install and operations | Decision |
|---|---|---|---|---|
| Embedded Python and SQLite | `VERIFIED` by a real child-process exit, replay, store, lease, migration, and reconciliation tests | Transactions, unique receipts, revision checks, leases, persisted timers, and schema 1 migration work at tested boundaries. | Python standard library, one transient process, no account. SQLite supports the target desktop platforms. | `BUILD` |
| Restate Server and Python SDK | `UNVERIFIED` locally. The `restate` executable was absent. | Journal replay, durable steps, timers, promises, retries, and invocation controls already exist. | Server is a separate process plus the Python service. Native install docs cover macOS and Linux. Windows packaging needs a real test. Server uses BSL 1.1; the Python SDK uses MIT. | `SPIKE`, then `INTEGRATE` only if embedded recovery fails or the domain grows |
| Temporal and Python SDK | `UNVERIFIED` locally. The `temporal` executable was absent. | Workflow history and replay, Activities, timers, Signals, Updates, and Queries cover the domain. Workflow Pause is still marked pre-release. | CLI supports macOS, Linux, and Windows. A local server, Worker, task queue, replay rules, and upgrades add more operational work than this controller needs. | `DEFER` |
| Provider-native sessions | Codex App Server no-model terminate/resume is `VERIFIED`; adapter conformance is covered separately. Claude native resume remains `UNVERIFIED` without authentication and a model budget. | Conversation continuity works. Sessions do not own cross-provider dependencies, external receipts, or controller timers. | Codex and Claude are separate optional host installs with their own auth and retention. | `INTEGRATE` as adapters |

## Acceptance dimensions

| Dimension | Embedded SQLite | Restate | Temporal | Provider-native sessions |
|---|---|---|---|---|
| One-command install and packaging | `VERIFIED` by runner wheel checks | `UNVERIFIED` locally | `UNVERIFIED` locally | Host install is separate; Codex is available locally |
| macOS, Linux, Windows | Standard-library plan; package checks cover only available hosts | Docs cover macOS/Linux; Windows `UNVERIFIED` | CLI docs cover all three; local execution `UNVERIFIED` | Host-dependent |
| Local repository and no cloud account | `VERIFIED` by local tests | Supported by docs, executable test absent | Supported by local server docs, executable test absent | Codex local session test `VERIFIED` |
| Crash recovery and idempotent actions | `VERIFIED` at the injected boundary | `UNVERIFIED` | `UNVERIFIED` | Session resume only `VERIFIED`; actions do not belong here |
| Pause, resume, cancel, timers, waits | Runner tests cover controls and waits | Docs describe primitives; executable test absent | Docs describe primitives; executable test absent | Provider interruption exists; controller pause and waits absent |
| Audit and migration | SQLite journal and schema tests | Runtime journal and upgrades need a spike | History replay and Worker upgrades need a spike | Transcript audit only; no controller migration |
| Size and operations | One transient Python process plus database | Server plus Python service | Server, Worker, task queue, and history | One optional host process per provider |
| License and maintenance | Python and SQLite ecosystem; project MIT | Server BSL 1.1, SDK MIT | Server and SDK licenses need release review | Provider terms and host versions apply |

Documentation-only cells are not execution evidence. In particular, a version
probe never upgrades Restate or Temporal from `UNVERIFIED`.

The Restate comparison must become executable before it can replace the
embedded choice. Use the same sequence: complete a fake provider action, commit
its receipt, kill the service, restart the runtime with persistent data, and
verify that the provider action is not repeated. Also exercise pause, resume,
cancel, a durable timer, and cleanup. Until that test exists, Restate remains a
documented alternative rather than an adopted dependency.

## Provider fit

Codex App Server exposes JSON-RPC methods for `thread/start`, `thread/resume`,
`thread/fork`, `turn/start`, `turn/interrupt`, `thread/compact/start`, and
`model/list`. Turn and item notifications form the stream. The comparison uses
`thread/start`, persists goal metadata without a turn, terminates App Server,
and calls `thread/resume` with the recorded thread ID. The official protocol
says clients must retain that ID. The adapter stores the returned thread ID as
a foreign session ID and derives usage from structured events. The official
documentation recommends the Codex SDK for automated jobs, while App Server is
the deeper client integration.

Claude Agent SDK has resumable and forked sessions, streaming input and output,
`Query.interrupt()`, model discovery, cost and usage fields, context usage, and
compact boundary events. Explicit compaction is an ordinary `"/compact"` turn.
The adapter must wait for `system/compact_boundary`; a successful result alone
does not prove that compaction happened. Session history does not restore the
filesystem. SkipHow must checkpoint task facts outside the provider transcript.

The Python code therefore uses injected transport protocols. It includes a
Codex App Server JSONL subprocess transport and selects the Claude Agent SDK
when that runtime is installed. The SDK transport keeps a persistent client,
uses typed interruption, and records `PreCompact` boundaries. If the SDK is
unavailable or invalid, the factory uses the structured Claude CLI fallback.
That fallback terminates its active process on interrupt and reports its weaker
compaction and interruption behavior in runtime status.

Model IDs come only from provider discovery or caller configuration. The core
contract contains semantic profiles and capability fields, but no provider
model names.

## Primary sources

Codex:

- [Codex App Server protocol and lifecycle](https://learn.chatgpt.com/docs/app-server)
- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk)
- [Codex non-interactive mode and resume](https://learn.chatgpt.com/docs/non-interactive-mode)

Claude:

- [Claude Agent SDK TypeScript reference](https://code.claude.com/docs/en/agent-sdk/typescript)
- [Claude Agent SDK sessions](https://code.claude.com/docs/en/agent-sdk/sessions)
- [Streaming input and interruption](https://code.claude.com/docs/en/agent-sdk/streaming-vs-single-mode)
- [Streaming output](https://code.claude.com/docs/en/agent-sdk/streaming-output)
- [Commands and compaction](https://code.claude.com/docs/en/agent-sdk/skills#commands-in-agent-sdk-sessions)
- [Cost and usage](https://code.claude.com/docs/en/agent-sdk/cost-tracking)
- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)

Restate:

- [Installation](https://docs.restate.dev/installation)
- [Journal and recovery concepts](https://docs.restate.dev/foundations/key-concepts)
- [Python durable steps](https://docs.restate.dev/develop/python/durable-steps)
- [Durable timers](https://docs.restate.dev/develop/python/durable-timers)
- [External events and promises](https://docs.restate.dev/develop/python/external-events)
- [Invocation pause, resume, and cancel](https://docs.restate.dev/services/invocation/managing-invocations)
- [Restate Server license](https://github.com/restatedev/restate/blob/main/LICENSE)
- [Python SDK and license](https://github.com/restatedev/sdk-python)

Temporal:

- [Workflow history and replay](https://docs.temporal.io/workflows)
- [Activities and idempotency](https://docs.temporal.io/activities)
- [Workflow message passing](https://docs.temporal.io/encyclopedia/workflow-message-passing)
- [Workflow Pause status](https://docs.temporal.io/encyclopedia/workflow/workflow-pause)
- [Cross-platform CLI and local server](https://docs.temporal.io/cli/setup-cli)
- [Production deployment model](https://docs.temporal.io/production-deployment)
- [Python SDK reference](https://python.temporal.io/)

## Revisit triggers

Repeat the Restate and Temporal spikes if SkipHow needs multi-host Workers,
hundreds of concurrent campaigns, server-side schedules, or operational SLOs.
Before then, adding either runtime would create more deployment state than the
campaign state it manages.
