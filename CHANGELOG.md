# Changelog

All notable changes to this project appear in this file.

## Unreleased

### Changed

- Added a Codex ChatGPT OAuth evaluation mode. It reuses the current Codex profile without copying credentials, requires an exact enabled cached plugin payload, forbids API-key and dollar-budget options, and caps host invocations with `--max-calls`.

## 0.9.0 (2026-08-25, preview)

Version 0.9.0 removes the Python runner introduced in 0.8. SkipHow is now one portable, owner-facing skill. Codex and Claude use the host's own sessions, goals, subagents, worktrees, resume support, and permission controls.

This is a breaking release. The `skiphow` executable, its SQLite state, runtime schemas, provider adapters, and runner configuration no longer exist. SkipHow does not provide a compatibility command or migrate runner state. Git history retains the removed implementation.

### Changed

- Kept one public `skiphow` entry point for discussion, capture, delivery, and task control. Requests use ordinary language instead of separate fix, CTO, idea, or automode commands.
- Made short tasks run in the current host session. Long work uses host-native goals and background tasks when the host provides them.
- Made GitHub Issues, pull requests, and Git the durable record for tracked work. Projects without GitHub can keep explicit capture requests in `.skiphow/inbox.md`.
- Replaced model names with the semantic `FAST`, `STANDARD`, and `DEEP` tiers. The root maps them only from current host metadata and otherwise inherits the current model with an `UNVERIFIED` selection result.
- Limited automatic merge to explicit unattended or end-to-end work. Required checks, reviews, repository rules, and exact-head checks still apply.
- Made pause, cancellation, and narrower authority cancel owned pending merge actions, and made recovery fail closed without trusted scope, authority, ownership, and exact state.
- Defined one deduplicated intake record as part of delivery authority for a material independent finding, without implementing or reprioritizing it.
- Rewrote the plugin policy, architecture, research notes, decisions, and README around the host-native design.

### Added

- Added an opt-in live evaluator for ten owner workflows. It loads an exact candidate and grades synthetic workspaces against external oracles. Mutable GitHub execution fails closed until an external boundary can prevent repository deletion while allowing required Git writes.
- Added recursive receipt redaction, exact installed-payload comparison, repository-free marketplace snapshots, and the package's MIT license text.

### Removed

- Removed the `skiphow` Python package and the `setup`, `intake`, `start`, `add-task`, `github-deliver`, `execute`, `worker`, `status`, `pause`, `resume`, `cancel`, `reconcile`, and `export` CLI commands.
- Removed SQLite run state, the supervisor, provider transports, model calibration, runtime verification, security journal, JSON runtime schemas, and runner-specific configuration.
- Removed the copied Claude skill shim and vendored workflow instructions. Both host packages now use the same canonical skill.
- Removed runner-specific tests and evals that did not install and exercise the exact candidate plugin.

### Verification status

- Deterministic repository and package checks remain in CI.
- Live Codex and Claude outcome checks remain opt-in. Implicit selection, owner-intent interpretation, host-native continuation, unattended GitHub delivery, autonomous model selection, and model-tier savings stay `UNVERIFIED` until exact 0.9 evidence covers them.

## 0.8.0 (unreleased development candidate)

This unpublished candidate explored a durable Python runner, SQLite state, provider adapters, and a larger evaluation harness. Version 0.9.0 removed that architecture. Git history preserves the implementation and migration details.

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
- Added package-proof receipt handling to doctor, host capability profiles, 20 repository outcome scenarios, five policy mutations, multi-trial aggregation code, and a machine-readable live receipt format.
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
