# ADR 0012: Codex effort per spawn and a portable timestamp rule

## Status

Superseded by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). SkipHow 2.0 does not
prescribe per-spawn roles, effort, or a portable timestamp schema; hosts retain those mechanics.

## Date

2026-08-26

## Context

Through 1.5 the Codex routing path was three role files copied into a project's `.codex/agents/` when the owner asked. An owner had to know that step existed. The Codex plugin manifest still accepts only `skills`, `apps`, and `mcpServers`, so a plugin cannot ship agents, and a user-level Codex agents entry would define `scout`, `builder`, and `reviewer` for every project on the machine.

Codex 0.149 resolves a delegate's model and reasoning effort from the spawn call first, then `[agents]` defaults, then the parent. Its multi-agent prompt states that `spawn_agent` accepts `reasoning_effort` when `fork_turns` is `"none"` or a number, and that skill instructions may set it. A baseline run of the 1.5 skill on a fixture with no role files already spawned the scout at `low` and the reviewer at `high` this way; the role files had become redundant.

The 1.5 timestamp rule named `date -u +%Y-%m-%dT%H:%M:%SZ`. That fixed fabrication but assumed a POSIX shell.

## Decision

- On Codex, SkipHow sets reasoning effort per spawn: `low` for `scout`, `high` for `reviewer`, the session's for `builder`, with `fork_turns="none"` and the brief as the message. No role files ship and nothing is written into the project for routing. Delegates share the session sandbox; the brief carries what they must not change.
- The `Recorded` line in intake blocks and checkpoints states the invariant: the UTC time read from the system clock as `YYYY-MM-DDTHH:MM:SSZ`, `unknown` when no clock can be read, never estimated. How to read the clock is left to the host and platform.
- `scripts/check.py` no longer expects `codex-agents/`.

## Consequences

Codex owners get effort routing with no setup and no repository files. Per-role sandboxes on Codex are gone; the read-only boundary for the scout and reviewer is an instruction, as it already was on the delegate's side. The timestamp rule names no shell, so nothing in it ties it to Unix; no native Windows run exists yet, and the `unknown` fallback remains unexercised.

## Rejected alternatives

- Writing the user-level Codex agents directory on first use: a user-global side effect that names three agents in unrelated projects.
- Writing `.codex/agents/` into the project on first delegation: repository pollution for a setting the spawn call already carries.
- A plugin or hook that installs role files: the manifest has no field for it, and it would be an installer for a host limitation.
- A timestamp helper script: two hosts, a shell, and a one-line invariant do not need one.

## Evidence

- [1.6 receipts](../research/2026-08-26/v1.6-receipts.md)
- Codex subagent documentation and the multi-agent prompt in the 0.149.1 binary, read on 2026-08-26

## Revalidation triggers

Revisit when Codex ships plugin agents or tier aliases, when a Codex receipt shows a delegate ignoring the spawn effort, or when a receipt records an estimated timestamp.
