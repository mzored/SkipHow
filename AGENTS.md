# Repository instructions

## Source material

Use current primary documentation for host CLI behavior, supported plugin formats, and security guidance. Do not preserve stale commands because they appear in an old issue or summary.

## Claims and verification

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>` so the repository-managed environment supplies the pinned dependencies. Before completion, run `python scripts/check.py` and `git diff --check`. These checks must remain local and deterministic. Do not run Codex, Claude Code, or another model from tests or CI.

Live outcome evaluations are a separate, opt-in release activity. They require explicit credentials and a run budget, write machine-readable receipts, and never run from `scripts/check.py` or CI. A missing live receipt stays `UNVERIFIED`.

For packaging changes, run `python scripts/check_hosts.py` to validate package structure and isolated installation in each available host. Report an unavailable host as `UNVERIFIED`. Host package checks do not prove that a model will interpret runtime instructions correctly.

## Portable packaging

Do not add personal paths, home-directory assumptions, private helpers, credentials, telemetry, MCP servers, or hooks without an approved product decision. The optional SkipHow runner may be packaged with the product, but direct plugin use must not require it. Keep one canonical workflow. Adapters may point to it but must not copy its policy.

For work that the owning product or technical workflow classifies as tracked development, route GitHub lifecycle operations through `github-task`. The owning workflow decides whether the work needs an issue or branch independently from its execution shape. Review follows the changed surface; orchestration follows coordination and recovery needs. Small fixes must not acquire lifecycle steps solely because they modify code.

Changes to packaging require package validation in both Codex and Claude Code when those hosts are available. Changes to `cto-run` use deterministic policy and repository tests. Support claims require fresh package evidence for the exact final state being claimed.
