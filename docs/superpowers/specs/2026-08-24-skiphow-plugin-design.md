# SkipHow plugin design

## Goal

Publish SkipHow as an open source collection of agent skills. The first release ships `cto-run`, a workflow for long-running software delivery with durable state, bounded delegation, independent review, and exact completion evidence.

Version `0.1.0` must work in Codex and Claude Code without local path edits. The repository will remain compatible with the Agent Skills directory format so more agent adapters can be added after they are tested.

## Product contract

- Codex and Claude Code are supported in the first release.
- `cto-run` runs only after explicit user invocation.
- The plugin contains no MCP server, telemetry, remote service, or credential flow.
- English is the source language for public documentation and skill instructions.
- MIT is the project license.
- New skills may join the same plugin when they represent tools the maintainer uses and recommends.
- Support claims require a reproducible validation or installation check for that agent.

## Hard constraints

- A clean clone cannot depend on a maintainer's home directory, agent configuration directory, or preinstalled personal script.
- Host policy and repository instructions outrank the skill.
- Product decisions remain with the user. The orchestrator owns technical choices within the approved runbook.
- The portable policy names capability roles, not vendor model names.
- One owner writes overlapping files. Integration remains serial.
- Completion claims require fresh evidence for the exact candidate commit.
- The durable run directory must be sufficient to resume after context loss or a new session.
- The core workflow must not rely on hooks. Codex and Claude Code do not share one hook runtime.

## Options considered

### Standalone skill repository

This is the smallest package. It works with generic Agent Skills installers, but it gives Codex and Claude Code no native plugin listing, marketplace metadata, or agent-specific invocation controls. It also becomes awkward once SkipHow contains several skills.

### Skills-only plugin with thin adapters

This keeps one portable workflow and adds small Codex and Claude Code entrypoints. Each host gets native metadata and explicit invocation controls. The plugin can grow without adding a server or a custom installer.

### Plugin with a bundled CLI or MCP server

A CLI could own journaling and launcher rendering. An MCP server could expose state and orchestration tools. Neither solves a requirement in the first release. Both add installation, security, compatibility, and maintenance work. The current shell launcher also assumes personal paths and has unsafe path substitution edge cases.

## Decision

Build a skills-only plugin with thin host adapters. Keep `cto-run` as the first user-facing skill. Move its operating policy, templates, and capability routing into packaged references. Do not ship the current launcher, hooks, or journal executable.

The model will create and update durable artifacts with the filesystem tools supplied by the host. This removes the hidden dependency on `run-journal` while preserving the state contract.

## Package layout

```text
SkipHow/
|-- .agents/plugins/marketplace.json
|-- .claude-plugin/
|   |-- marketplace.json
|   `-- plugin.json
|-- .codex-plugin/plugin.json
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |-- pull_request_template.md
|   `-- workflows/
|-- adapters/
|   `-- claude/
|       `-- skills/cto-run/SKILL.md
|-- docs/
|   |-- architecture.md
|   `-- superpowers/
|-- skills/
|   `-- cto-run/
|       |-- SKILL.md
|       |-- agents/openai.yaml
|       |-- assets/
|       |   `-- runbook-template.md
|       `-- references/
|           |-- operating-policy.md
|           |-- state-contract.md
|           |-- capability-routing.md
|           `-- host-notes.md
|-- tests/test_repository.py
|-- AGENTS.md
|-- CHANGELOG.md
|-- CODE_OF_CONDUCT.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- README.md
`-- SECURITY.md
```

The Codex manifest loads `./skills/`. `agents/openai.yaml` disables implicit invocation. The Claude manifest points to `./adapters/claude/skills/`, which prevents Claude Code from auto-loading the standard entrypoint. Its wrapper uses `disable-model-invocation: true` and loads the canonical workflow from `skills/cto-run/`.

The adapter contains no orchestration policy. A test fails if it stops pointing at the canonical entrypoint.

## Skill behavior

### Invocation

The user invokes `cto-run` with a runbook path, a durable run directory, and an optional target. The skill derives a run directory only when the project and campaign are unambiguous.

### Boot

The orchestrator reads the packaged operating policy, the project runbook, and repository instructions. It records their paths and hashes in durable state. It then reconstructs the current repository, tracker, CI, worktree, and external state from primary evidence.

### Execution

The root routes work by capability role:

- Mechanical workers perform bounded read-only extraction and deterministic commands.
- Implementation workers own scoped changes, ordinary debugging, and corpus synthesis.
- CTO review workers handle architecture decisions, repeated anomalies, the root role, and the final independent integration review.

Concrete model selection belongs to the host adapter or active runtime. The policy never requires a model name that another agent cannot provide.

### Durable state

Every run stores a small recoverable record:

```text
run-directory/
|-- state.json
|-- journal.jsonl
|-- briefing.md
|-- FINAL.md
|-- decisions/
|-- evidence/
`-- receipts/
```

The policy defines required fields and append rules. It allows a host to use native file tools, shell commands, or a later helper program. The file format remains stable across hosts.

### Recovery

After context loss or restart, the root rereads the policy and runbook, rebuilds state from the run directory, and verifies that record against the repository and external systems. Summaries and prior agent reports remain claims until checked.

### Stop conditions

The run ends only when its terminal condition is verified. It may stop earlier for a product decision, missing authority for an irreversible action, or a blocker that cannot be resolved safely. A blocked lane does not stop independent authorized work.

## Error handling

- Missing or unreadable contracts stop the affected run before project changes.
- Ambiguous project identity or target triggers one product question.
- A failed worker packet returns to its existing owner with evidence. The root does not create recursive review chains.
- Repeated anomalies trip a circuit breaker and require root cause analysis before another attempt.
- External outages preserve local progress and mark the exact system, action, and retry condition in durable state.
- Dirty worktrees and unrelated user changes remain untouched unless the runbook puts them in scope.

## Repository and release workflow

The GitHub repository will be `mzored/SkipHow`, public, with issues enabled. A public Project v2 named `SkipHow` will track work through the existing task workflow. The bootstrap issue will cover the first plugin release.

Development uses an issue branch and an isolated worktree after the design commit. The integration diff receives one fresh no-history review. The issue closes from the merge commit. Version `0.1.0` then receives an annotated tag and GitHub release.

Repository metadata will include a concise description and topics for Codex, Claude Code, agent skills, plugins, and orchestration.

## Verification

The release gate includes:

- Python repository contract tests for manifests, paths, version sync, required files, forbidden personal paths, and adapter linkage.
- The bundled OpenAI skill and plugin validators.
- `claude plugin validate` for the plugin and marketplace.
- A Codex discovery check in a temporary profile.
- A Claude Code marketplace installation check in an isolated home directory.
- A source scan for personal paths, unfinished placeholders, and stale version strings.
- Markdown link checks for local references.
- One independent review over the exact integration diff.

GitHub Actions runs deterministic repository tests on pull requests and pushes to `main`. Host CLI smoke checks remain release gates when those CLIs are available. CI does not download or authenticate proprietary agents.

## Dependency decision

Repository tests need a YAML parser for skill frontmatter and `agents/openai.yaml`. Adopt PyYAML `6.0.3` instead of writing a partial parser. The existing `cto-run` policy audit verified its MIT license, September 2025 release, multiple maintainers, stable version, and lack of known advisories as of 2026-08-24. Tests must use `yaml.safe_load`.

No runtime dependency ships with the plugin.

## Success criteria

- `mzored/SkipHow` is public and installable through its Codex and Claude Code marketplace files.
- Codex and Claude Code discover `cto-run` only as an explicit user action.
- A clean installation contains every referenced policy, template, and adapter file.
- No shipped file refers to a personal absolute path or private helper.
- The same operating policy drives both supported hosts.
- Tests and both host validators pass for the released commit.
- Release `v0.1.0` documents installation, invocation, limitations, and upgrade steps.

## Architecture verdict

`INTEGRATE` the portable core of the existing `cto-run` into a skills-only SkipHow plugin. Keep host differences in thin adapters and defer MCP, hooks, and a bundled runtime until a real skill needs them.
