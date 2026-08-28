# Changelog

All notable changes to SkipHow 2.x appear in this file. Earlier release notes remain available on [GitHub Releases](https://github.com/mzored/SkipHow/releases).

## 2.3.0 (2026-08-28)

### Added

- `decomposition` is now its own method, with a trigger a run can evaluate before it starts: the parts of the work would land, be verified, or be reviewed separately. A unit is right-sized when one person can observe its behavior end to end, verify it alone, and review it in one pass. Units are cut through the layers, never along them, because a unit named for a schema, an endpoint, or a screen cannot be demonstrated alone and forces the whole result into one late review.
- Splitting is judgment, not a stage. Work whose parts land, get verified, and get reviewed together stays one unit, so small work keeps completing without ceremony.
- Mechanical changes with a wide blast radius are exempt from vertical slicing and sequenced expand, migrate, contract, so the project keeps working at every step.
- A unit states its outcome and what would show it true, and does not prescribe files, names, or steps. Only genuine blocking edges are recorded; order presented as dependency is what serializes work that could run concurrently.
- A decomposition is checked before it is acted on, against the original request and the records themselves, read back cold or by a delegate, because whoever drew the split is the worst judge of whether it holds.
- Delegate briefs carry the outcome, its completion condition, the boundary the delegate works inside, and the instruction to return a blocking unknown rather than settle it alone. A rule not written into the brief does not reach the delegate.
- A returned question is the orchestrator's to settle. It reaches the owner only under the kernel's existing bar, so many lanes do not become many interruptions.
- Lanes that write at the same time need separate working trees, or they run one at a time.

### Changed

- The kernel now requires reconciling split work against the request before reporting: what finished with evidence, what is blocked, and what is deliberately left and on what ground. Reporting success while a part was never started is a false completion. Leaving a unit for later needs a reason the owner would accept, and preferring not to do it is not one.
- `intake` reads the tracker as well as writing to it, and the kernel trigger now reaches work the project already has on record. Recorded work is reconciled against live project state; the agent settles what it can settle and raises only an unmade product decision or a part of the result no item covers.
- A batch of observations is grouped by cause before it becomes records. Several reports with one cause are one unit of work; one report with several causes is several. The owner's own description stays in the record.
- Deduplication is stated by repair rather than by wording: reports one fix resolves are merged, problems fixed separately stay separate even on the same screen.
- Recording a decomposition follows the same authority as any other record. A request only to plan, compare, or advise returns the split in the answer and writes nothing.
- `delegation` covers how units run; `decomposition` owns what they are and which edges genuinely block.

### Fixed

- `docs/evidence.md` stated that none of the 2.2.0 behavior was `UNVERIFIED`, which asserted the opposite of what it meant, and listed releases out of order.
- `docs/guide.md` named only review and diagnose as recording nothing, while the kernel's read-only list is wider.
- `THIRD_PARTY_NOTICES.md` omitted `delegation`, `project-setup`, and `technical-design` from the adapted references, and would have omitted the two added here.

### Evidence

- `python scripts/check.py` and `git diff --check` passed. Claude package validation and isolated install passed. Codex package validation is `UNVERIFIED` from a bare local invocation; CI runs it against the pinned validator on the pull request.
- Two independent reviews of the staged change found the first draft's method reachable only through triggers that excluded the scenarios it was written for, a write obligation with no authority gate, a self-contradicting deduplication rule, and an escape hatch that authorized the false completion it forbade. All were corrected before release.
- The runtime behavior is `UNVERIFIED`. No receipt yet shows large work split into independently verifiable units, concurrent lanes reconciling completely, or one cause producing one record.

## 2.2.1 (2026-08-28)

### Fixed

- Isolated checkouts land inside the project again. `delegation` now names where a worktree goes: the host's own mechanism first, then the location the repository already ignores, confirmed ignored before anything is created there, and a temporary directory only when the repository offers neither. A worktree beside the repository is never correct, because it escapes the project's ignore rules and cleanup and accumulates unnoticed.
- The kernel carries the boundary in one sentence, because the 1.8.0 audit measured that a reference which does not load governs nothing. Version 1.x kept this rule only in a reference, and 2.0.0 removed that reference without replacing it, leaving no placement rule at all.
- Removing an isolated checkout is never forced. A refusal is evidence that something still owns it.

### Evidence

- Deterministic checks and both host package validators passed.
- Reported from the owner's machine: twenty worktrees belonging to three repositories had accumulated beside them, while all three repositories keep an ignored `.worktrees/` directory of their own. Attribution to a specific package version is `UNVERIFIED`; the missing rule is not.

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
