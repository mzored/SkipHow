# Architecture

SkipHow ships one portable workflow and thin host adapters. The portable workflow is the canonical source. Host adapters only tell each host how to reach it.

## Canonical skill

`skills/cto-run/SKILL.md` is the canonical `cto-run` skill. It requires explicit user invocation, reads the operating policy and the project runbook, and creates durable records before important waits, handoffs, integrations, and context loss.

The skill has no MCP server, telemetry, remote service, credential flow, hook, or bundled command-line program. Hosts supply filesystem access, command execution, task controls, and any connected services.

## Claude Code adapter

The Claude Code adapter at `adapters/claude/skills/cto-run/SKILL.md` disables model invocation. It directs Claude Code to the canonical skill instead of copying orchestration policy. Codex loads the canonical `skills/` directory directly.

This keeps behavior in one place. A change to the workflow belongs in the canonical skill, not in an adapter.

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

For the full rationale and package layout, read the [plugin design](superpowers/specs/2026-08-24-skiphow-plugin-design.md).
