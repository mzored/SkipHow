# Research from 2026-08-26

This directory records the 1.0 release audit, the review that set the direction for 1.1, and the 1.1 to 1.6 receipts and the paired evaluations.

| Topic | What it records |
| --- | --- |
| [Release 1.0 audit](release-1.0-audit.md) | Audit findings, current primary documentation, verified package facts, workflow pins, security settings, and remaining evidence gaps |
| [Real-task application audit](real-task-application-audit.md) | Observed policy-application gaps in tracked delivery, durable privacy decisions, finding triage, and dirty-state attribution |
| [System review](system-review.md) | Critical review of 1.0.1 against the owner's brief: inert routing, continuity, policy density, brittle tests, doc duplication, hygiene |
| [Host routing and continuity](host-routing-and-continuity.md) | Verified Claude Code and Codex facts on per-agent model and effort, plugin agents and hooks, compaction, and unattended launch |
| [Prior-art mechanics](prior-art-mechanics.md) | Concrete mechanics from nine projects worth borrowing or leaving out |
| [1.1 brief](v1.1-brief.md) | The work order that 1.1.0 implemented |
| [1.1 receipts](v1.1-receipts.md) | Real runs on the 1.1.0 candidate: routing, compaction continuity, small task, findings outside scope |
| [1.2 receipts](v1.2-receipts.md) | Real runs on the 1.2.0 candidate: small task, feature, reuse, findings without GitHub, batch intake and end-to-end GitHub delivery, resume |
| [1.3 receipts](v1.3-receipts.md) | Real runs on the 1.3.0 candidate: the first Codex receipts, continuity across an observed compaction, a large request delivered end to end |
| [1.4 receipts](v1.4-receipts.md) | Real runs on the 1.4.0 candidate: findings fixed by observation, handoff deleted after compaction, a three-Issue epic, Codex builder delegation |
| [1.5 receipts](v1.5-receipts.md) | Real runs on the 1.5.0 candidate: clock timestamps, bounded delivery without the delivery reference, Codex scout and reviewer |
| [1.6 receipts](v1.6-receipts.md) | Real runs on the 1.6.0 candidate: Codex effort per spawn with no role files, a portable clock timestamp |
| [Paired evaluation](paired-eval.md) | Three tasks with and without the skill on the same model: turns, cost, time, where records went |

The accepted campaign and engineering decision is in [ADR 0006](../../decisions/0006-host-native-campaign-and-engineering-policy.md). The routing and continuity decision is [ADR 0007](../../decisions/0007-host-adapters-for-routing-and-continuity.md); the evaluation decision is [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md); the 1.2 reviewer and reference layout decision is [ADR 0009](../../decisions/0009-reviewer-inherits-and-one-engineering-reference.md); the 1.3 hook and Codex evidence decision is [ADR 0010](../../decisions/0010-two-matcher-hook-and-codex-project-loading.md); the 1.4 findings, Codex role file, and repository instruction decision is [ADR 0011](../../decisions/0011-findings-tag-codex-role-files-neutral-repo-instructions.md); the 1.6 per-spawn effort and timestamp decision is [ADR 0012](../../decisions/0012-per-spawn-effort-and-portable-timestamps.md). Earlier research for the host-native rewrite remains under [2026-08-25](../2026-08-25/README.md).

Facts in this directory describe the dated audit. Host behavior, repository settings, action tags, and vendor formats can change. Recheck the linked primary sources before changing packaging or making a support claim.
