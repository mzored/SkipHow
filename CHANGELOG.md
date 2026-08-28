# Changelog

All notable changes to SkipHow 2.x appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

## 2.0.2 (2026-08-28)

### Changed

- Cut the tracked repository from 108 files to 50 without changing the owner skill, internal methods, or continuity hook.
- Rewrote the README for a faster first read and moved installation, design, decisions, and evidence into four focused documents.
- Replaced the 1.x ADR and research tree with concise current summaries and immutable links to the complete 2.0.1 archive.
- Removed the contributor-only dogfood analyzer, its transcript-format tests, and the unused run-summary script.
- Grouped retained tests by package structure, deterministic checks, and host checks.

## 2.0.1 (2026-08-28)

### Changed

- Replaced the 1.x workflow contract with one owner-facing skill and a small set of focused internal methods.
- Kept authority, autonomy, preservation, and verified completion in the owner kernel.
- Removed magic phrases, fixed routes, model tiers, standing roles, and mandatory process that strong agents can choose for themselves.
- Kept shared policy independent of provider model IDs and host-specific routing.
- Required explicit owner authority for production, public releases, credentials, payments, access changes, and destructive actions.
- Updated deterministic checks for the one-skill package, continuity hook, source attribution, versions, links, and portability.

### Evidence

- Deterministic checks and both host package validators passed.
- Claude isolated installation passed. Codex isolated installation was `UNVERIFIED` because managed source policy rejected the local marketplace.
- Six retained Codex observations covered a small project change, read-only diagnosis and product choice, protected-action boundaries, and a visual interaction. See the [current evidence](docs/evidence.md) for limits and durable source links.
