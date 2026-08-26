# Architecture decisions

This directory records accepted SkipHow architecture decisions. [How it works](../how-it-works.md) describes the current design. The [2026-08-26 research](../research/2026-08-26/README.md) records the 1.0 to 1.6 release evidence. The [2026-08-25 research](../research/2026-08-25/README.md) records the host-native rewrite that preceded it.

An accepted decision stays in place until a later ADR replaces it. Correct factual errors and broken links in place, but do not rewrite the decision to hide an architectural change.

## When a decision earns an ADR

An ADR is for a commitment that is expensive to reverse, or that rejects an alternative a future contributor would otherwise propose again. It is not a release artifact, and a release is not a reason to write one: 0005 through 0016 each accompanied a release, which is how this directory grew past the size of the package it governs.

A policy edit — a sentence tightened, moved so it loads earlier, or deleted because it contradicted another — is recorded by its changelog section and by the field-audit receipt that motivated it. When such an edit answers a question an ADR already owns, amend that ADR; do not open a competing one. This is the same rule the product itself gives owners under **Record proportionately** in `references/decision.md`.

Two sections carry the weight and every ADR keeps them: `## Rejected alternatives`, so a settled argument is not refought, and `## Revalidation triggers`, so evidence the project already agreed to act on can be found by grep. The `dogfood` skill reads both before it proposes anything.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-one-owner-entry.md) | Use one owner-facing SkipHow skill | Accepted |
| [0002](0002-host-native-execution.md) | Use host-native execution | Accepted |
| [0003](0003-semantic-model-routing.md) | Route models by semantic capability | Accepted |
| [0004](0004-github-lifecycle-and-authority.md) | Define GitHub lifecycle and authority | Accepted, amended by 0014 |
| [0005](0005-fail-closed-release-evaluation.md) | Keep release evaluation repository-free and fail closed | Superseded by 0008 (claims policy stands) |
| [0006](0006-host-native-campaign-and-engineering-policy.md) | Keep campaign and engineering policy host-native | Accepted, amended by 0009 and 0016 |
| [0007](0007-host-adapters-for-routing-and-continuity.md) | Resolve model tiers and session continuity in host adapters | Accepted, amended by 0009, 0010, and 0012 |
| [0008](0008-receipts-over-a-live-harness.md) | Prove model behavior with receipts, not a live harness | Accepted |
| [0009](0009-reviewer-inherits-and-one-engineering-reference.md) | Reviewer inherits the session model; one engineering reference | Accepted |
| [0010](0010-two-matcher-hook-and-codex-project-loading.md) | One hook with two matcher groups; Codex evidence through project-level loading | Accepted, amended by 0011 |
| [0011](0011-findings-tag-codex-role-files-neutral-repo-instructions.md) | Tagged findings, shipped Codex role files, neutral repository instructions | Accepted, amended by 0012 and 0013 |
| [0012](0012-per-spawn-effort-and-portable-timestamps.md) | Codex effort per spawn, no role files; portable timestamp rule | Accepted |
| [0013](0013-read-only-requests-save-nothing.md) | Read-only requests report findings `UNSAVED`; records need a granting request | Accepted |
| [0014](0014-conform-to-the-tracker-classification.md) | Conform to the tracker's classification, do not configure it | Accepted, amended in 1.11.0 |
| [0015](0015-unconditional-invariants-live-in-the-root.md) | Unconditional invariants live in the root skill | Accepted, amended in 1.10.0 |
| [0016](0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) | Decomposition needs a trigger a run can evaluate | Accepted, amended in 1.10.0 |
