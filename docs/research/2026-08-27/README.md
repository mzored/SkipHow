# Research from 2026-08-27

This directory records the second audit of real SkipHow sessions run in other repositories, the frozen
same-day candidate census that triggered the 2.0 simplification, current architecture and analogue research, one
owner report from the field, the 1.12.0 invocation receipts, and the 1.13.0 parallel review round.

The 2.0 material describes an unpublished release candidate. Marketplace installation still resolves to
1.14.2 until 2.0 is published.

| Topic | What it records |
| --- | --- |
| [Owner report](owner-report-commit-language.md) | A run writing Russian commit messages into an English-history repository, and what the 1.10.0 package said about commits: nothing |
| [Field audit](field-audit-2026-08-27.md) ([coverage sidecar](field-audit-2026-08-27.receipts.json)) | Earlier delivery and read-only sessions plus a fail-closed census that retains all 37 root owner-chat candidates and aggregates nested subagent evidence instead of presenting it as extra chats. It scopes 18 other-project sessions with owner turns: 16 have an observable marker on the local 2026-08-27 date and two adjacent August 26 sessions remain date-unverified. Eight have one exact observed version identity, four are partially unknown, one is mixed, and five are unknown. The two bounded UI runs repeated the missing routine endpoint, but their exact governing contract identity is unverified; live-UI workflows and other confounders also prevent a speed or tool-count claim |
| [2.0 architecture and analogues](runtime-policy-simplification.md) | Why the selected portable architecture is one top-level owner skill with thirteen internal Markdown methods, current Agent Skills and host formats, Matt Pocock's pinned collection and nontechnical UX caveats, the cross-host sibling-skill blocker, the old budget history, and the commit-qualified 1.14-to-2.0 package-shape measurement |
| [2.0 Codex receipts](v2.0-codex-receipts.md) | Six clean project-local one-off observations against source commit `b2196d0bd3eeca1f542cbd8af3e1b45639aad29d` and owner-skill tree `95d908988208b9fcc1d285fe1ca1c5c681c4da1b`: one small committed change, two read-only outcomes, both sides of a local protected-action fixture, and the named visual create-choice change completed as a tested clean commit. Every fixture had one project skill. The earlier 14-skill batch is invalid, and real external delivery remains unverified |
| [1.13 receipts](v1.13-receipts.md) | Five external reviews of the standing package run at once — what each lane found, which findings were confirmed against primary sources or by planting the defect, and the six that were rejected on inspection |
| [1.14 host CLI receipt](v1.14-host-cli-receipt.md) | Static help evidence for unattended command shapes; full unattended delivery remains unverified |
| [1.12 receipts](v1.12-receipts.md) | What `codex review` and headless `claude` actually accept, the 1.12.0 candidate reviewed through the cross-host rung it adds, and the unequal boundary the two hosts give that pass — Codex sandboxes it, plan mode does not stop the reviewed repository's own hooks |

These records amend or motivate [ADR 0004](../../decisions/0004-github-lifecycle-and-authority.md), [ADR 0009](../../decisions/0009-reviewer-inherits-and-one-engineering-reference.md), [ADR 0014](../../decisions/0014-conform-to-the-tracker-classification.md), [ADR 0015](../../decisions/0015-unconditional-invariants-live-in-the-root.md), [ADR 0016](../../decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md), [ADR 0017](../../decisions/0017-autonomous-routine-delivery-uses-owned-worktrees.md), and [ADR 0018](../../decisions/0018-autonomous-kernel-and-independent-task-skills.md).
The receipts policy it follows is [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Earlier
field evidence is under [2026-08-26](../2026-08-26/README.md).

Facts in this directory describe the dated audit. Host behavior, plugin resolution, and vendor formats can
change. Recheck the linked primary sources before changing packaging or making a support claim.
