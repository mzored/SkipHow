# Architecture decisions

This directory records accepted SkipHow architecture decisions. [How it works](../how-it-works.md) describes
the current design. The [2026-08-27 research](../research/2026-08-27/README.md) records the field revalidation
and 2.0 architecture, the [2026-08-26 research](../research/2026-08-26/README.md) records the 1.0 to 1.6
release evidence, and the [2026-08-25 research](../research/2026-08-25/README.md) records the host-native
rewrite that preceded it.

An accepted decision stays in place until a later ADR replaces it. Correct factual errors and broken links in place, but do not rewrite the decision to hide an architectural change.

## When a decision earns an ADR

An ADR is for a commitment that is expensive to reverse, or that rejects an alternative a future contributor would otherwise propose again. It is not a release artifact, and a release is not a reason to write one: 0005 through 0016 each accompanied a release, which is how this directory grew past the size of the package it governs.

A policy edit — a sentence tightened, moved so it loads earlier, or deleted because it contradicted another — is recorded by its changelog section and by the field-audit receipt that motivated it. When such an edit answers a question an ADR already owns, amend that ADR; do not open a competing one. [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md) carries the current authority and record boundary.

Two sections carry the weight and every ADR keeps them: `## Rejected alternatives`, so a settled argument is not refought, and `## Revalidation triggers`, so evidence the project already agreed to act on can be found by grep. The `dogfood` skill reads both before it proposes anything.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-one-owner-entry.md) | Use one owner-facing SkipHow entry | Accepted as amended by 0018; one top-level owner skill stands and fixed routes are retired |
| [0002](0002-host-native-execution.md) | Use host-native execution | Accepted; fixed routes, worktrees, and roles superseded by 0018 |
| [0003](0003-semantic-model-routing.md) | Route models by semantic capability | Superseded by 0018 |
| [0004](0004-github-lifecycle-and-authority.md) | Define GitHub lifecycle and authority | Lifecycle superseded by 0018; tracker and authority principles stand |
| [0005](0005-fail-closed-release-evaluation.md) | Keep release evaluation repository-free and fail closed | Superseded by 0008 (claims policy stands) |
| [0006](0006-host-native-campaign-and-engineering-policy.md) | Keep campaign and engineering policy host-native | Campaign procedure superseded by 0018; host-native principle stands |
| [0007](0007-host-adapters-for-routing-and-continuity.md) | Resolve model tiers and session continuity in host adapters | Routing superseded by 0018; continuity hook stands |
| [0008](0008-receipts-over-a-live-harness.md) | Prove model behavior with receipts, not a live harness | Accepted |
| [0009](0009-reviewer-inherits-and-one-engineering-reference.md) | Reviewer inherits the session model; one engineering reference | Superseded by 0018 |
| [0010](0010-two-matcher-hook-and-codex-project-loading.md) | One hook with two matcher groups; Codex evidence through project-level loading | Both kernel-loading hook groups and receipt policy stand; 1.x project-loading workaround superseded by 0018 |
| [0011](0011-findings-tag-codex-role-files-neutral-repo-instructions.md) | Tagged findings, shipped Codex role files, neutral repository instructions | Tags and roles superseded by 0018; neutral instructions stand |
| [0012](0012-per-spawn-effort-and-portable-timestamps.md) | Codex effort per spawn, no role files; portable timestamp rule | Superseded by 0018 |
| [0013](0013-read-only-requests-save-nothing.md) | Read-only requests save nothing; records need a granting request | Read-only boundary stands; routes and tags superseded by 0018 |
| [0014](0014-conform-to-the-tracker-classification.md) | Conform to the tracker's classification, do not configure it | Tracker principle stands; fixed markers and schema superseded by 0018 |
| [0015](0015-unconditional-invariants-live-in-the-root.md) | Unconditional invariants live in the root skill | Authority, autonomy, and completion stay in root; budgets, routes, gates, and fixed procedure superseded by 0018 |
| [0016](0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) | Decomposition needs a trigger a run can evaluate | Superseded by 0018 |
| [0017](0017-autonomous-routine-delivery-uses-owned-worktrees.md) | Autonomous routine delivery uses owned worktrees and exact aggregate evidence | Superseded by 0018; protected promotion boundary stands |
| [0018](0018-autonomous-kernel-and-independent-task-skills.md) | Use one autonomous owner skill with focused internal methods | Accepted for 2.0.0 |
