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

`plugins/skiphow/skills/cto-run/SKILL.md` remains the technical execution workflow. It requires explicit invocation by the user, `develop`, or `fix` after a repair qualifies as a durable campaign. It reads the operating policy and project runbook and creates durable records before important waits, handoffs, integrations, and context loss.

The skill has no MCP server, telemetry, remote service, credential flow, hook, or bundled command-line program. Hosts supply filesystem access, command execution, task controls, and any connected services.

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
