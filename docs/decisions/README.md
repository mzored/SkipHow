# Architecture decisions

This directory records accepted SkipHow architecture decisions. [How it works](../how-it-works.md) describes the current design. The [2026-08-26 research](../research/2026-08-26/README.md) records the 1.0 to 1.6 release evidence. The [2026-08-25 research](../research/2026-08-25/README.md) records the host-native rewrite that preceded it.

An accepted decision stays in place until a later ADR replaces it. Correct factual errors and broken links in place, but do not rewrite the decision to hide an architectural change.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-one-owner-entry.md) | Use one owner-facing SkipHow skill | Accepted |
| [0002](0002-host-native-execution.md) | Use host-native execution | Accepted |
| [0003](0003-semantic-model-routing.md) | Route models by semantic capability | Accepted |
| [0004](0004-github-lifecycle-and-authority.md) | Define GitHub lifecycle and authority | Accepted, amended by 0014 |
| [0005](0005-fail-closed-release-evaluation.md) | Keep release evaluation repository-free and fail closed | Superseded by 0008 (claims policy stands) |
| [0006](0006-host-native-campaign-and-engineering-policy.md) | Keep campaign and engineering policy host-native | Accepted, amended by 0009 |
| [0007](0007-host-adapters-for-routing-and-continuity.md) | Resolve model tiers and session continuity in host adapters | Accepted, amended by 0009, 0010, and 0012 |
| [0008](0008-receipts-over-a-live-harness.md) | Prove model behavior with receipts, not a live harness | Accepted |
| [0009](0009-reviewer-inherits-and-one-engineering-reference.md) | Reviewer inherits the session model; one engineering reference | Accepted |
| [0010](0010-two-matcher-hook-and-codex-project-loading.md) | One hook with two matcher groups; Codex evidence through project-level loading | Accepted, amended by 0011 |
| [0011](0011-findings-tag-codex-role-files-neutral-repo-instructions.md) | Tagged findings, shipped Codex role files, neutral repository instructions | Accepted, amended by 0012 and 0013 |
| [0012](0012-per-spawn-effort-and-portable-timestamps.md) | Codex effort per spawn, no role files; portable timestamp rule | Accepted |
| [0013](0013-read-only-requests-save-nothing.md) | Read-only requests report findings `UNSAVED`; records need a granting request | Accepted |
| [0014](0014-conform-to-the-tracker-classification.md) | Conform to the tracker's classification, do not configure it | Accepted |
| [0015](0015-unconditional-invariants-live-in-the-root.md) | Unconditional invariants live in the root skill | Accepted |
