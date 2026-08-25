# Repository instructions

## Source material

Use current primary documentation for host CLI behavior, supported plugin formats, and security guidance. Do not preserve stale commands because they appear in an old issue or summary.

When research changes the architecture, product contract, security policy, or model routing, record the verified findings under `docs/research/` and update or add the relevant ADR before completion. Routine research notes do not need persistence.

## Claims and verification

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>` so the repository-managed environment supplies the pinned dependencies. Before completion, run `python scripts/check.py` and `git diff --check`. These checks must remain local and deterministic. Do not run Codex, Claude Code, or another model from tests or CI.

Live outcome evaluations are a separate, opt-in release activity. They require explicit credentials and a run budget, write machine-readable receipts, and never run from `scripts/check.py` or CI. A missing live receipt stays `UNVERIFIED`.

Tests, checks, and live gates must never create or delete a repository. Keep deterministic coverage local. A live GitHub gate may mutate only an explicitly named, pre-provisioned sandbox that is distinct from the candidate repository, and its credentials must not have repository creation or deletion authority.

For packaging changes, run `python scripts/check_hosts.py` to validate package structure and isolated installation in each available host. Report an unavailable host as `UNVERIFIED`. Host package checks do not prove that a model will interpret runtime instructions correctly.

## Portable packaging

Do not add personal paths, home-directory assumptions, private helpers, credentials, telemetry, MCP servers, or hooks without an approved product decision. Package one canonical SkipHow skill. Host manifests and adapters may point to it but must not copy its policy. Use host capabilities for direct and long-running work. Do not add a SkipHow runner, daemon, task database, provider bridge, or model catalog without an approved product decision.

For work that the owning product or technical workflow classifies as tracked development, route GitHub lifecycle operations through `github-task`. The owning workflow decides whether the work needs an issue or branch independently from its execution shape. Review follows the changed surface; orchestration follows coordination and recovery needs. Small fixes must not acquire lifecycle steps solely because they modify code.

Changes to packaging require package validation in both Codex and Claude Code when those hosts are available. Support claims require fresh package evidence for the exact final state being claimed.
