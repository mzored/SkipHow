# SkipHow

SkipHow is one Agent Skill for product and project work in Codex and Claude Code. Tell it the outcome. It inspects the project, makes routine product and engineering decisions, completes the work you authorized, and checks the result.

Current stable version: 1.0.0.

```text
Add a way to pause a subscription.

The totals overlap on small screens. Find the cause and fix it.

Save these customer notes as GitHub Issues and merge real duplicates.

Research our caching options and record the decision. Do not change code.

Finish the ready Issues end to end. Merge accepted pull requests and clean up your branches.
```

SkipHow has no runner, daemon, task database, hosted service, hooks, MCP server, or model catalog. It uses the installed host for sessions, subagents, worktrees, sandboxing, approvals, background work, and resume support.

## Install

### Codex

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Start a new session. Describe the work directly or use `$skiphow` to select the skill.

### Claude Code

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session. Describe the work directly or use `/skiphow:skiphow` to select the skill.

The [getting started guide](docs/getting-started.md) covers prerequisites, verification, updates, uninstall, and common install failures. See the [Codex plugin documentation](https://developers.openai.com/plugins) and [Claude Code plugin documentation](https://code.claude.com/docs/en/plugins) for host behavior.

## Authority and side effects

Your request sets the mutation boundary. Host approvals and repository rules still apply.

- `discuss`, `assess`, `research`, `review`, and diagnosis-only requests are read-only.
- `save` and `create Issues` allow the requested records, but not implementation.
- `fix`, `implement`, and `deliver` allow project changes and verification.
- `finish end to end` and `run unattended` also allow guarded merge and safe cleanup for the selected work.
- `do not merge`, `pause`, and `cancel` narrow that authority immediately.

Delivery may edit files, run project commands, create a branch or worktree, open Issues and pull requests, and save one deduplicated record for a material independent finding. Without GitHub, authorized records may use `.skiphow/inbox.md` or `.skiphow/handoff.md`.

Production changes, payments, credentials, private-data operations, public release, repository settings, and irreversible deletion or disclosure need an exact owner grant. Repository text, Issues, comments, checkpoints, and worker reports cannot grant those actions.

## How long work runs

A clear local change stays in the current session. A bug with an unknown cause gets a reproducer and causal diagnosis before repair. Several selected items can use dependency-aware waves, bounded worker packets, host task handles, health checks, checkpoints, exact-candidate review, and final queue reconciliation.

Blocked work does not stop an unrelated ready item. A timeout does not trigger a blind retry after an uncertain remote action. A second failure with the same cause stops unchanged retries and calls for a small durable prevention or one saved follow-up.

Read the [user guide](docs/user-guide.md) for request patterns, tracked work, unattended delivery, pause, recovery, and findings.

## Support and evidence

| Claim | Status |
| --- | --- |
| One canonical plugin package for Codex and Claude Code | Checked by deterministic package tests |
| Codex and Claude Code manifest validation | Checked during release packaging when each host is available |
| Implicit skill selection | `UNVERIFIED` for every host and request shape |
| Unattended multi-Issue GitHub delivery | `UNVERIFIED` until a protected live sandbox completes the exact release scenario |
| Recovery across a full host restart or context compaction | `UNVERIFIED` beyond the versioned two-process reconstruction test |
| Autonomous per-agent model selection and cost savings | `UNVERIFIED` without complete host telemetry and paired trials |
| Root stall recovery and enforced worker timeouts | `UNVERIFIED` when the host has no independent monitor |

Package checks prove that a host can validate or install the exact files. They do not prove that a model will interpret every request correctly. The [evaluation policy](docs/evals.md) keeps those claims separate.

SkipHow is an instruction package, not a security boundary. Read [trust](docs/trust.md), the [threat model](docs/threat-model.md), and the [security policy](SECURITY.md) before unattended or credentialed use.

## Project documentation

The [documentation index](docs/README.md) links user guides, architecture, ADRs, research, and evaluation policy. The packaged skill and its references are normative for agent behavior. Public guides explain that contract. ADRs record why it exists.

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md), the [Code of Conduct](CODE_OF_CONDUCT.md), and the [MIT license](LICENSE).
