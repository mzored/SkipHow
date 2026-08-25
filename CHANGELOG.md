# Changelog

All notable changes to this project appear in this file.

## Unreleased

### Changed

- Replaced live model evaluations with direct deterministic tests for the runtime policy contracts.
- Limited host checks to package validation and isolated installation. Package evidence no longer implies skill activation or model behavior.
- Made `scripts/check.py` prepare and reuse an environment outside the repository when the current Python lacks the pinned check dependencies.
- Made Codex package checks install from the repository Git origin and reject a remote `HEAD` that differs from the local commit.
- Made the official Codex package validator reuse the repository-managed Python when the system interpreter lacks its dependencies.

### Removed

- Removed the Codex and Claude Code live eval runners, outcome scenarios, multi-trial release gate, and live eval receipts.

## 0.7.0

### Changed

- Replaced runtime reads of vendored upstream methods with compact, self-contained diagnosis, testing, technical review, and codebase design capabilities. Source copies, licenses, and pinned attribution remain source-only.
- Reduced every measured route closure. Common software routes are at least 23 percent smaller than v0.6; diagnosis and optional capability routes are at least 37 percent smaller.
- Made readiness, delegation lane contracts, operation health fields, review, and durable records conditional on the work that needs them.
- Added direct execution for non-software project artifacts inside the existing `CHANGE` intent, with source, render, or preview evidence suited to the artifact.
- Added verbatim request alignment, verification-gap checks, evidence-backed finding types, and precise in-scope completion semantics.
- Reworked repository outcome evals around correctness, mutation boundaries, required evidence, forbidden side effects, and separately reported economy signals.
- Replaced host-name assumptions with a semantic capability contract and single-agent fallback for bounded work.
- Split GitHub candidate search from semantic duplicate decisions, separated linked-branch creation from delivery provenance, and made Project status mapping explicit and optional.
- Corrected support documentation so CLI availability is not package proof and untested hosts or products remain `UNVERIFIED` or unclaimed.

### Added

- Added `scripts/context_budget.py`, a committed decreasing baseline, runtime-to-upstream lint, and CI ratchet for route context.
- Added `.skiphow/config.json` as the only optional config contract, with strict validation for tracker, Project, and campaign path settings.
- Added package-proof receipts to doctor, host capability profiles, 20 repository outcome scenarios, five policy mutations, multi-trial release aggregation, and machine-readable live receipts.
- Added campaign-only goal ancestry, budget envelopes, cancellation, idempotent lane claims, checkpoints, orphan recovery, and final reconciliation.
- Added lazy contracts for extensions, consequential behavior deltas, source-backed product decisions, and explicitly maintained verified project context.

### Removed

- Removed `.skiphow/config.yml`, `strict_lifecycle`, runtime upstream loading, implicit substring duplicate claims, and automatic Project status assumptions.
- Removed package-validated support claims that were not backed by a fresh receipt.

### Migration from 0.6

- If `.skiphow/config.yml` exists, move supported values to `.skiphow/config.json`, replace disabled Project values with `null`, and delete `strict_lifecycle`.
- GitHub adapter callers should use `find_candidates`, `create_linked_branch`, and `record_delivery`; Project status updates now require an explicit field and option mapping.
- Treat existing host support statements as historical only. Generate fresh package and live outcome receipts for the exact 0.7 candidate before publishing support claims.

## 0.6.0

### Changed

- Replaced the public workflow catalog with one conversational `skiphow` entrypoint for answer, capture, decision, change, repair, and continuation requests.
- Clear changes now execute from a lightweight delivery brief without mandatory shaping, tracking, Owner approval, product review, or acceptance receipts.
- Made extended product records, independent product review, and product acceptance conditional on consequential decisions or repository policy.
- Made GitHub Issues the optional default persistence integration and GitHub Projects an explicitly configured view.
- Replaced blocking preflight semantics with a read-only doctor that reports optional capabilities independently.
- Split deterministic local checks from optional host validation and added version consistency checks.
- Added activation, routing, repository outcome, forbidden-side-effect, and policy mutation eval coverage.
- Simplified dependency diligence and campaign state so optional fields and artifacts appear only when triggered.

### Added

- Added `.skiphow/inbox.md` as the local fallback for explicit capture requests with no configured tracker.
- Added narrow optional `github_issues.py`, `github_project.py`, and `doctor.py` adapters.
- Added a support matrix, privacy notes, diagnostics, update, rollback, and uninstall guidance.

### Removed

- Removed default lifecycle hooks and the monolithic GitHub lifecycle helper.
- Removed runtime handling of the legacy `Human Gate` Project field. Existing fields are left untouched and ignored.
- Removed separate public Codex skills and Claude wrappers for internal workflows.

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
