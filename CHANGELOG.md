# Changelog

All notable changes to this project appear in this file.

## 0.5.0

### Changed

- Simplified technical routing to normal `EXECUTE`, focused `DIAGNOSE`, and durable `CAMPAIGN` paths.
- Replaced universal risk levels with concrete changed surfaces that determine evidence and review without selecting orchestration.
- Made tracking lazy, combined scope control with terminal finding dispositions, and limited revalidation to semantically invalidated evidence.
- Generalized completion and product-acceptance receipts from commit-only gates to exact delivered-state identities, with recovery guidance for existing campaign state.
- Focused subagents on context isolation, independent review, and genuinely parallel work instead of label-driven ceremony.
- Made GitHub Issues the durable work identity and a minimal Project the default human-facing queue, with Issue-only degraded operation and no mandatory `Human Gate` schema.
- Added vertical-slice and fog-of-war campaign decomposition, strict domain-glossary and ADR thresholds, and a verified human-action handoff.

### Added

- Added disposable `prototype` and intent-preserving `resolving-merge-conflicts` capabilities.
- Added `setup` for reusing or bootstrapping the standard minimal GitHub Project.

## 0.4.0

### Added

- The internal `cto` controller for direct, tracked-direct, or durable technical delivery.
- Internal testing, technical-review, and codebase-design capabilities adapted from pinned MIT sources.
- Product Director acceptance for user-visible Product Contract work.
- A read-only `preflight` workflow for local tools, GitHub authentication, board schema, hooks, and host commands.
- A 24-scenario behavioral corpus, a structured Codex runner, and one deterministic release-verification entrypoint.

### Changed

- `develop`, `fix`, and technical maintenance now route through the CTO instead of treating `cto-run` as all technical execution.
- Risk controls validation and review depth. Durability controls whether work uses `cto-run`.
- CI now runs package metadata, YAML, source, Markdown-link, behavioral-corpus, repository-test, and whitespace checks through `scripts/verify_release.py`.
- Python 3.10 or newer is now the documented minimum for the bundled lifecycle helper.

## 0.3.0

### Added

- The internal `github-task` lifecycle adapter for tracked GitHub work.
- Portable Codex and Claude Code hooks for linked-branch status and compact Project v2 operations.

### Changed

- `fix`, `develop`, and `cto-run` now decide when GitHub tracking applies before handing lifecycle work to `github-task`.
- GitHub lifecycle no longer selects implementation methods, test policy, review depth, or verification cadence.

## 0.2.0

### Added

- The `skiphow`, `idea`, `shape`, `develop`, `fix`, and `diagnose` skills.
- Adaptive defect routing through direct repair, internal diagnosis, bounded product decisions, or durable CTO campaigns.
- Product Contract review and immutable delivery campaign guidance.
- Claude Code adapters for every shipped skill.

### Changed

- Claude Code now loads the full SkipHow skill adapter directory.
- `diagnose` is now an internal capability used only when the cause is unclear.

## 0.1.0

### Added

- The `cto-run` skill for explicit, durable software campaigns.
- Codex and Claude Code plugin adapters.
- Repository contract tests, contributor policy, and CI.
