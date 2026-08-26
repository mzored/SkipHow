# Repository instructions

## Source material

Use current primary documentation for host CLI behavior, supported plugin formats, and security guidance. Do not preserve stale commands because they appear in an old issue or summary.

When research changes the architecture, product contract, security policy, or model routing, record the verified findings under `docs/research/` and update or add the relevant ADR before completion. Routine research notes do not need persistence.

## Claims and verification

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>` so the repository-managed environment supplies the pinned dependencies. Before completion, run `python scripts/check.py` and `git diff --check`. These checks must remain local and deterministic. Do not run Codex, Claude Code, or another model from tests or CI.

Model behavior is proven by receipts under `docs/research/<date>/` (ADR 0008), produced on purpose with the host's own permission and budget controls, never from `scripts/check.py` or CI. A behavior no receipt has shown stays `UNVERIFIED`. Tests and checks must never create or delete a repository.

For packaging changes, run `python scripts/check_hosts.py` to validate package structure and isolated installation in each available host. Report an unavailable host as `UNVERIFIED`. Host package checks do not prove that a model will interpret runtime instructions correctly.

## Portable packaging

Do not add personal paths, home-directory assumptions, private helpers, credentials, telemetry, or MCP servers without an approved product decision. The package carries exactly one hook (the read-only `SessionStart` continuity hook) and exactly three agent adapters (`scout`, `builder`, `reviewer`) under ADR 0007; anything more needs a new ADR. Package one canonical SkipHow skill. Host manifests and adapters may point to it but must not copy its policy. Use host capabilities for direct and long-running work. Do not add a SkipHow runner, daemon, task database, provider bridge, or model catalog without an approved product decision.

For work that the owning product or technical workflow classifies as tracked development, use the canonical GitHub lifecycle in `plugins/skiphow/skills/skiphow/references/github.md`. The owning workflow decides whether the work needs an issue or branch independently from its execution shape. Review follows the changed surface; orchestration follows coordination and recovery needs. Small fixes must not acquire lifecycle steps solely because they modify code.

Changes to packaging require package validation in both Codex and Claude Code when those hosts are available. Support claims require fresh package evidence for the exact final state being claimed.
