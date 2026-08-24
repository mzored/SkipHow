# Architecture

SkipHow ships portable workflows and thin host adapters. Each workflow under `plugins/skiphow/skills/` is canonical. Host adapters only tell each host how to reach it.

## Canonical skills

The plugin separates owner intent, product direction, diagnosis, delivery control, and technical execution:

- `skiphow` routes the request and enforces the Owner, Product Director, and CTO authority boundary.
- `idea` captures without shaping.
- `shape` produces a reviewed Product Contract without prescribing implementation.
- `develop` freezes approved work and starts an immutable delivery campaign.
- `fix` routes defects through a direct repair, internal diagnosis, product decision, or CTO campaign according to evidence.
- `diagnose` is the internal diagnostic loop for causes that remain unclear after initial inspection.
- `cto-run` executes the campaign and keeps durable state.
- `github-task` performs GitHub issue and Project v2 lifecycle operations only after the owning workflow classifies work as tracked.

`plugins/skiphow/skills/cto-run/SKILL.md` remains the technical execution workflow. It requires explicit invocation by the user, `develop`, or `fix` after a repair qualifies as a durable campaign. It reads the operating policy and project runbook and creates durable records before important waits, handoffs, integrations, and context loss.

The plugin has no MCP server, telemetry, remote service, credential flow, or bundled runtime. Hosts supply filesystem access, command execution, task controls, and connected services. GitHub lifecycle support adds local plugin hooks and a bundled Python helper. It requires Python 3, `git`, and authenticated `gh` 2.93.0 or newer. Claude Code on native Windows additionally uses the Git Bash shipped by Git for Windows so one shell-form hook can select `python3`, `python`, or `py -3` without duplicating lifecycle policy.

## GitHub lifecycle integration

Verdict: `INTEGRATE`.

SkipHow uses the official GitHub CLI for authentication, Issues, Project v2 mutations, and narrow GraphQL queries. One bundled standard-library Python helper filters Project v2 responses down to the board, queue, item, or verification line the workflow needs. Codex discovers `plugins/skiphow/hooks/hooks.json` at its default plugin path. The Claude manifest points to the same canonical file, and its root script is a small adapter to the canonical helper inside the Codex package.

The alternative was a second GitHub client library such as PyGithub. It would add dependency installation, version management, and another authentication path, but it would not replace host hook handling or the Project v2 GraphQL queries. A remote service was rejected because lifecycle state already lives in GitHub and the plugin does not need another credential or availability boundary. A personal helper path was rejected because installed plugins must be portable.

Dependency check recorded on 2026-08-24: the [GitHub CLI repository](https://github.com/cli/cli) declares the MIT license, [v2.98.0](https://github.com/cli/cli/releases/tag/v2.98.0) was released on 2026-08-20, and the project is past pre-1.0. The public contributor history has several active contributors, but the number of maintainers is unverified because the repository does not publish that role. GitHub's high-severity advisories [GHSA-8xvp-7hj6-mcj9](https://github.com/cli/cli/security/advisories/GHSA-8xvp-7hj6-mcj9) and [GHSA-p2h2-3vg9-4p87](https://github.com/cli/cli/security/advisories/GHSA-p2h2-3vg9-4p87) affect ranges through v2.92.0 and v2.61.0, so SkipHow requires v2.93.0 or newer. The exact validation host used v2.97.0.

The hooks guard adopted lifecycle state only. `PreToolUse` prevents branch creation when a tracked item's Human Gate is not `No`; it fails open when the repository or issue is not on an adopted board. `Stop` catches a linked task branch whose board item is still unstarted. The skill sets `In Progress` only after branch creation and linkage are confirmed, avoiding remote mutation from host PostToolUse events that do not expose shell success consistently. The owning workflow remains responsible for deciding whether tracking exists and for all engineering work.

Hosts may disable or refuse plugin hooks through their own policy. In that case the `github-task` skill still exposes explicit lifecycle commands, but automatic claim and stop checks are unavailable.

## Claude Code adapter

Claude Code loads the adapters under `adapters/claude/skills/`. Each adapter directs Claude Code to its canonical skill instead of copying policy. The `cto-run` adapter disables model invocation; the owner-facing routing skills may activate when their descriptions match. Codex installs the nested `plugins/skiphow/` package and loads its `skills/` directory directly. Keeping that package below the repository root prevents Claude Code from discovering both copies.

This keeps behavior in one place. A workflow change belongs in its canonical skill, not in an adapter.

## Capability roles

The operating policy uses capability roles instead of provider-specific model names:

- `MECHANICAL` workers handle bounded extraction and deterministic commands.
- `IMPLEMENTATION` workers own scoped changes, ordinary debugging, and synthesis.
- `CTO_REVIEW` workers make architecture decisions, investigate repeated anomalies, and perform the final independent integration review.

The active host maps available agents to those roles and records any limitation in a receipt.

## Durable state

A run directory must contain these root files:

```text
state.json
journal.jsonl
briefing.md
FINAL.md
```

It also contains `decisions/`, `evidence/`, and `receipts/`. After recovery, the root agent rebuilds the current picture from these files and primary systems. Prior summaries and worker reports are claims until checked.

## Release gates

Before release, the repository runs contract tests, package validators, a source scan, and local Markdown link checks. The release process also checks Codex discovery and Claude Code marketplace installation in isolated environments. CI runs the deterministic repository checks only. It does not download or authenticate proprietary hosts.
