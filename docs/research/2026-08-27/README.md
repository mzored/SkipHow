# Research from 2026-08-27

This directory records the second audit of real SkipHow sessions run in other repositories, one owner report from the field, the 1.12.0 invocation receipts, and the 1.13.0 parallel review round.

| Topic | What it records |
| --- | --- |
| [Owner report](owner-report-commit-language.md) | A run writing Russian commit messages into an English-history repository, and what the 1.10.0 package said about commits: nothing |
| [Field audit](field-audit-2026-08-27.md) | Two delivery sessions and one read-only session judged against the exact versions they ran: model routing that resolves, delegation and handoff rules that did not load, owner-turn expansion that stayed in one shared checkout, a collision that forced commit plumbing, and what automatic compaction actually costs |
| [1.13 receipts](v1.13-receipts.md) | Five external reviews of the standing package run at once — what each lane found, which findings were confirmed against primary sources or by planting the defect, and the six that were rejected on inspection |
| [1.14 host CLI receipt](v1.14-host-cli-receipt.md) | Static help evidence for unattended command shapes; full unattended delivery remains unverified |
| [1.12 receipts](v1.12-receipts.md) | What `codex review` and headless `claude` actually accept, the 1.12.0 candidate reviewed through the cross-host rung it adds, and the unequal boundary the two hosts give that pass — Codex sandboxes it, plan mode does not stop the reviewed repository's own hooks |

These records amend or motivate [ADR 0004](../../decisions/0004-github-lifecycle-and-authority.md), [ADR 0009](../../decisions/0009-reviewer-inherits-and-one-engineering-reference.md), [ADR 0014](../../decisions/0014-conform-to-the-tracker-classification.md), [ADR 0015](../../decisions/0015-unconditional-invariants-live-in-the-root.md), [ADR 0016](../../decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md), and [ADR 0017](../../decisions/0017-autonomous-routine-delivery-uses-owned-worktrees.md).
The receipts policy it follows is [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Earlier
field evidence is under [2026-08-26](../2026-08-26/README.md).

Facts in this directory describe the dated audit. Host behavior, plugin resolution, and vendor formats can
change. Recheck the linked primary sources before changing packaging or making a support claim.
