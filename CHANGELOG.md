# Changelog

All notable changes to SkipHow 2.x appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

## 2.2.0 (2026-08-28)

### Added

- `execution-health`: give a long-running step an expected duration and a no-progress signal, treat a breach as information, classify the cause before correcting it, and stop after three genuine attempts against one hypothesis rather than trying a fourth.
- A reuse-first order in `technical-design`: search what the repository already has, then platform primitives, official SDKs, mature components, managed services, and a bounded spike before custom code. Building carries the burden of naming the requirement the alternatives fail.
- Recurring defect patterns in `diagnosing-bugs`, including work that is not idempotent on rerun, partial success reported as completion, a default branch absorbing what belongs elsewhere, and mocks that have drifted from the behavior they stand for.
- A statement in the kernel of what does not count as evidence: reasoning that a change should work, a path that looks equivalent, a suite that passed without knowing what each check covers, a screen that opened, or an absence of errors.

### Changed

- `testing` requires a regression test to close the bug class: observed failing against the unfixed code, asserting the violated invariant at the layer that owns it, covering each boundary a bad value crossed. Verification is staged by reach rather than rerun wholesale, and an intermittent pass is a defect until classified.
- `reviewing-changes` separates making a change from certifying it. Risky results are confirmed independently of the account that produced them, and an important defect is fixed before the work continues rather than carried forward as accepted.
- Never silence an unexplained failure by raising a timeout, adding a retry, disabling a check, weakening an assertion, or reaching for a bypass flag.
- `AGENTS.md` and `docs/decisions.md` record that method depth is limited by whether a method loads, not by its length.

### Evidence

- Deterministic checks and both host package validators passed.
- Every behavior in this release is `UNVERIFIED`, including whether the added depth changes an outcome. See the [current evidence](docs/evidence.md).

## 2.1.0 (2026-08-28)

### Added

- A project change now also grants the durable records the project keeps for that work: the agreed outcome, the state a later session needs to resume it, and one carry-forward record for a material problem the change leaves unfixed. A separable finding previously reached only the chat transcript, so the next session paid to rediscover it.
- `project-setup`: one owner question settles where tracked work lives and who may see it, recorded in the project's own agent instructions and not asked again.
- `technical-design`: recover the real constraints, check volatile facts against primary sources, compare options that genuinely differ, and decide without returning the choice to the owner.
- `delegation`: shape large work as a task graph rather than a list, serialize parts that touch the same shared surface, and point delegates at context instead of copying it.
- Versioning and release rules in `AGENTS.md`, including one release per coherent change set rather than one per package edit.

### Changed

- `product-decisions` now establishes the intended outcome and its acceptance criteria before substantial work, asking only where different readings would produce a materially different product.
- `continuity` treats the project's own record of tracked work as the continuation surface. `.skiphow/handoff.md` remains the fallback for a project with no such destination.
- `intake` records carry the impact, what surfaced the problem, the evidence already gathered, and the explanations already ruled out, using the tracker's own structure.
- Durable text the project keeps follows the language and conventions of its own history rather than the conversation's.

### Evidence

- Deterministic checks and both host package validators passed.
- The new runtime behavior is `UNVERIFIED`. No receipt yet covers recording a finding once, resuming from a record, or the absence of added ceremony on small work. See the [current evidence](docs/evidence.md).

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
