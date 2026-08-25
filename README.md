# SkipHow

Give SkipHow an ordinary-language outcome. The plugin makes routine product and technical decisions, performs authorized work, and reports evidence.

```text
Add a way to pause a subscription.

Payments are sometimes charged twice. Find the cause, fix it, and verify it.

Here are twenty customer notes. Group duplicates and save actionable work.
```

No tracker, Project, Python, `gh`, setup command, or hook is required for direct plugin work. Small and bounded requests stay inside the current host session.

The 0.8.0 worktree is an unreleased release candidate. It includes an optional local runner for durable campaigns. Deterministic tests cover its store, supervisor, recovery, routing, provider contracts, and refusal paths. Live multi-trial behavior and model-routing savings remain `UNVERIFIED` until receipts exist for the exact released candidate. Claude authentication and live Claude outcomes are also `UNVERIFIED`.

## Install with Codex

Add this repository as a personal marketplace, then open the plugin browser:

```sh
codex plugin marketplace add mzored/SkipHow
codex
# Open /plugins, select SkipHow, and install it.
```

Start a new session after installation. See the [official plugin guide](https://learn.chatgpt.com/docs/plugins).

## Install with Claude Code

```text
/plugin marketplace add mzored/SkipHow
/plugin install skiphow@skiphow
```

Start a new session after installation. If Claude Code reports an on-disk change, run `/reload-plugins`. See the [official Claude Code plugin guide](https://code.claude.com/docs/en/discover-plugins).

## Optional durable runner

Install the runner from a checkout with Python 3.11 or newer:

```sh
python -m pip install .
skiphow start "Finish the ready backlog" --task "Implement the first deliverable"
# Copy the run_id from the JSON output, then run:
skiphow execute RUN_ID --provider codex --max-duration 1800 --max-cost 10
```

The CLI stores state in `.skiphow/runs/runner.sqlite3` by default. `execute` supervises a run in the foreground until it settles or reaches a configured limit. `worker` processes one ready frontier. The CLI also supports `setup`, `intake`, `start`, `add-task`, `status`, `pause`, `resume`, `cancel`, `reconcile`, and `export`. Direct plugin use does not start the runner.

The runner has:

- revision-checked run and task transitions;
- SQLite transactions, an append-only event journal, snapshots, leases, and recovery capsules;
- foreground supervision, lease heartbeats, external-wait polling, bounded retry, circuit breaking, invocation time and reported-cost ceilings, and state-derived final reconciliation;
- provider-session resume with recovery-capsule fallback when the old session is unavailable;
- provider-neutral Codex and Claude session adapters; and
- secret redaction before runner state is written.

The package also contains provider-neutral routing and security libraries. The CLI supervisor uses model discovery, a selected semantic profile, and host permission mapping. Durable outcome calibration, filesystem allowlists, and the generic ownership registry are not wired into every supervisor action.

The supervisor is a foreground process. It does not install a daemon or require a SkipHow cloud account. Provider credentials stay in their host or provider stores. Restart after a machine reboot requires the user or another process to invoke `skiphow execute` again.

## Product intake

`INTAKE` accepts one signal, an explicit list, or a batch of bugs, ideas, questions, risks, technical debt, and feedback. The Python API preserves raw-record and atom provenance, observed evidence, timestamps, and links. It can group related signals, return at most twenty duplicate candidates, record an explicit duplicate decision, shape actionable work items, and validate Epic dependency graphs. Semantic duplicate and priority decisions still belong to the product controller.

GitHub Issues are canonical when tracked delivery is required and GitHub is configured. Direct plugin capture can use `.skiphow/inbox.md`. The Python Intake ledger uses `.skiphow/intake/signals.jsonl` and `.skiphow/intake/work-items.json`. Both write only when authorized. A GitHub Project is an optional view.

## Configuration

Project-safe settings use `.skiphow/config.json`:

```json
{
  "schema_version": 2,
  "tracker": {"type": "auto", "project": null},
  "delivery": {"merge_policy": "never", "cleanup": "merged_only"},
  "findings": {"persist": "local"},
  "campaign_root": ".skiphow/runs"
}
```

The parser still reads v1 configuration. Explicit migration writes a backup before replacing it. Personal cost preferences, limits, provider catalogs, and model IDs belong in the user's SkipHow configuration directory. Credentials do not belong in either file.

`skiphow setup` writes product-level choices without asking for a schema, library, provider model, or Git strategy. Provider details remain optional advanced personal configuration.

## Support matrix

Package, adapter, and live behavior evidence are separate.

| Product | Package format | Adapter conformance | Live outcomes |
| --- | --- | --- | --- |
| Codex CLI and desktop | Codex plugin | deterministic contract tests | multi-trial release outcomes `UNVERIFIED` |
| Claude Code | Claude plugin | deterministic contract tests | auth and live outcomes `UNVERIFIED` |
| Optional Python runner | source package | deterministic local tests | external campaigns `UNVERIFIED` |
| Codex IDE | not claimed | not claimed | not claimed |
| ChatGPT Chat and Work | policy excluded | not claimed | not claimed |

An unavailable host is `UNVERIFIED`. Package validation does not prove that a model interprets instructions correctly.

## Checks and evals

```sh
python scripts/check.py
python scripts/check.py --offline
python scripts/check_hosts.py --output path/to/host-proof.json
```

The first command creates and reuses a pinned dependency cache outside the repository. `--offline` never accesses the network. The host check records package evidence as `VERIFIED`, `UNVERIFIED`, or `FAILED`.

The deterministic check also runs from a source archive without `.git`; file validation falls back to the archive tree and Git diff evidence is unavailable. Release identity and exact-host installation still require a Git checkout.

The opt-in GitHub gate uses a clean committed candidate and an owned disposable private repository. It proves Issue, native dependency, pull request, CI, merge, branch cleanup, forced interruption, and resume. It is separate from `scripts/check.py` because it mutates remote state. See [GitHub lifecycle](docs/github-lifecycle.md).

Live eval harness v2 binds release mode to the exact twenty-scenario registry, validates a clean candidate identity, supports Codex and Claude adapters, grades returned observations, and fails the aggregate when a trial fails. It still does not provision each scenario fixture or independently collect final-state observations. Those release outcomes remain `UNVERIFIED`. See [evaluation and release evidence](docs/evals.md).

## Design and trust

The [architecture](docs/architecture.md) describes the thin semantic kernel, direct path, optional durable runner, provider adapters, and integrations. [Trust and operations](docs/trust.md) and the [threat model](docs/threat-model.md) cover processes, state, credentials, protected actions, cancellation, cleanup, and abuse cases.

More detail is in [intake](docs/intake.md), [operations](docs/operations.md), [model routing](docs/model-routing.md), [GitHub lifecycle](docs/github-lifecycle.md), and [prior art](docs/prior-art.md).
