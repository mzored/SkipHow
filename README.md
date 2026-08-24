# SkipHow

Give one ordinary-language request. SkipHow makes routine product and technical decisions, performs the authorized work, and returns evidence for the result.

```text
Add a way to pause a subscription. Make the routine product and technical decisions and implement it.

Payments are sometimes charged twice. Find the cause, fix it, and verify the result.

Save this idea for later without expanding it: a monthly customer report.
```

No tracker, Project, Python, `gh`, setup command, or hook is required. SkipHow has no telemetry or remote service. It uses the files, commands, and connected services already available in the host, subject to the host and repository permissions.

## Install with Codex

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Start a new Codex task in a project and describe the outcome. SkipHow is available in Codex CLI and the Codex desktop project workflow.

## Install with Claude Code

```sh
claude plugin marketplace add mzored/SkipHow
claude plugin install skiphow@skiphow
```

Open a project and describe the outcome. The plugin exposes one public skill, `skiphow`; internal workflows are loaded only when needed.

## What SkipHow decides

SkipHow resolves routine reversible product details, architecture, dependencies, implementation, testing, review, sequencing, and integration. It asks one focused question only when the choice belongs to the Owner.

The Owner keeps authority over vision, audience, portfolio and business priority, material scope, commercial constraints, cost or risk commitments, protected actions, and irreversible external actions.

Analysis, research, review, diagnosis-only, and planning requests are read-only unless you ask to save or change something.

## How work is handled

A clear feature goes straight from a small internal delivery brief to implementation and scenario evidence. It does not require a tracker item, product contract, reviewer ceremony, or acceptance receipt.

A consequential product decision can use a longer decision record and independent product review. A hard bug gets focused diagnosis before repair. Work gets durable campaign state only when coordination, session recovery, dependency waits, or parallel work needs it.

These are internal choices. You do not select a mode or command.

## Optional persistence and GitHub

When you explicitly ask to save an idea or finding, SkipHow uses the repository's configured tracker. With a GitHub origin and authenticated `gh`, it can create a GitHub Issue without a Project. With no tracker, it can use `.skiphow/inbox.md` as the canonical local fallback.

A GitHub Project is an optional view. SkipHow connects or creates one only when you ask. It never scans all of your Projects to guess which one to use, and Project status does not block completed code.

Optional overrides may live in `.skiphow/config.yml`:

```yaml
tracker: auto
project: disabled
strict_lifecycle: false
campaign_root: .skiphow/runs
```

The file is not required. See [architecture](docs/architecture.md) for the adapter contract and campaign details.

## Support matrix

| Product | Support |
| --- | --- |
| Codex CLI | Supported and package-validated |
| Codex desktop project workflow | Supported through the same Codex plugin package |
| Claude Code | Supported and package-validated |
| Codex IDE extension | Plugin packaging is not supported |
| ChatGPT Work | Not claimed until repository outcome evals pass with its available tools |

Core work needs a host that can inspect a project and, for change requests, edit files and run the project's checks. Optional GitHub persistence needs authenticated `gh`. Optional helper scripts support Python 3.10 through 3.13, but Python is not a core requirement.

## Trust, privacy, and removal

SkipHow sends no telemetry and runs no background service. It may read or change local project files and run local commands when the request authorizes that work. It reads or changes GitHub only for explicit persistence, existing tracked work, repository-required lifecycle work, or requested setup. The default package installs no lifecycle hooks.

See [trust and operations](docs/trust.md) for data access, diagnostics, updates, rollback, and uninstall instructions.

## Maintainer checks

```sh
python scripts/check.py
python scripts/check_hosts.py
```

The first command is deterministic and local. It does not require a Codex host validator. The second reports unavailable host proof as `UNVERIFIED`; release CI requires the configured official Codex validator.

Routing, activation, and repository outcome corpora live under `plugins/skiphow/evals/`. Offline validation runs through `scripts/check.py`. Paid live runs are opt-in:

```sh
python scripts/run_codex_evals.py --execute
python scripts/run_claude_evals.py --execute
python scripts/run_outcome_evals.py --host codex
python scripts/run_outcome_evals.py --host claude
```

## Project documents

- [Architecture](docs/architecture.md)
- [Trust and operations](docs/trust.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [MIT License](LICENSE)
