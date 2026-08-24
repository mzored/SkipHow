---
name: develop
description: Select approved product work and hand it to the internal CTO controller for proportionate delivery.
---

# develop

Act as the delivery handoff between Product Director and CTO. The Product Director chooses the approved work. The CTO decides how to deliver it.

Use `references/delivery-runbook.md` only when the CTO selects a durable campaign. Reuse the same run directory when resuming. The internal CTO workflow is `../cto/SKILL.md`. It uses normal `EXECUTE`, temporary `DIAGNOSE`, or `CAMPAIGN` after inspection. Do not create a campaign or invoke `cto-run` before that decision.

`develop` owns approved-work selection. The CTO owns execution, including whether GitHub tracking is required. `github-task` handles only lifecycle operations after that classification.

## Resolve the request

- With no scope, select the highest-priority coherent workset from the canonical product-approved or ready queue.
- With natural-language scope, match it to approved items. Do not require issue IDs.
- With `all-ready`, pass the current ready queue as one bounded program to the CTO. The CTO decides whether it needs durable orchestration.
- With `resume` or a run directory, pass the existing durable campaign to the CTO for `cto-run` recovery without selecting new work.
- With `drain`, pass successive approved worksets to the CTO. Re-read the current queue only after the current workset reaches its terminal state. Never add work to a durable campaign.

## Hand off approved work

1. Resolve approved work from the request and repository's product source of truth. Read a tracker only when it owns that approved work or status must change. Read the current product strategy, item priority, dependencies, and exact Product Contract revisions.
2. Let the Product Director choose a coherent workset tied to one product outcome. Resolve ordinary product trade-offs without asking the Owner.
3. Freeze the selected workset, its exact Product Contract revisions, exclusions, and source snapshot. Hand this immutable delivery brief to the CTO with the repository target. Do not create durable state yet.
4. Let the CTO inspect the work and choose `EXECUTE` or `CAMPAIGN`, using `DIAGNOSE` first only when a cause is genuinely unknown. Campaign routing follows coordination and recovery needs. Changed surfaces determine testing and review.
5. Only when the CTO selects `cto-run`, create a durable run directory according to repository convention. Write `campaign.md` with:

   ```text
   Goal
   <one product outcome>

   Included
   <tracker identifiers and immutable Product Contract revisions>

   Priority order
   <product order with reasons>

   Explicitly excluded
   <everything considered but outside this campaign>

   Source snapshot
   <tracker revision, timestamp, and relevant commit>
   ```

6. When included work is tracker-owned, mark those items as in development only after the frozen brief exists, subject to the CTO's lifecycle classification.
7. Let the CTO execute normal work or the canonical `cto-run` workflow with `references/delivery-runbook.md`, the run directory, and repository target. The durable campaign snapshot is authoritative for its scope.
8. Route implementation choices to the CTO. Route product questions to the Product Director. Escalate only a true Owner decision, protected action, missing authority, or external prerequisite.
9. When the CTO verifies the terminal condition, including Product Director acceptance when the Product Contract requires it, update any tracker-owned items and report the completed product outcome. For `drain`, select the next workset only now.

Do not copy the CTO operating policy, rewrite its technical plan, or absorb newly approved work into an active campaign.
