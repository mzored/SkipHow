---
name: skiphow-bug
description: Find and fix a reported defect at its cause, including the sibling paths that share that cause. Use for bug fixes and recurring failures; a diagnosis-only request stays read-only. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow bug

Fix the reported defect at its cause, together with every other path the same cause breaks. Before consequential work, and again after any context compaction, load the [SkipHow CTO kernel](../skiphow/SKILL.md) by invoking the `skiphow` skill where the host has a skill tool, otherwise by reading it, unless its full text is already in context; a summary is not its text. It governs authority, scope, delegation, review, and delivery throughout this workflow.

## Diagnose first

Make no fix until the cause is shown. Use [diagnosis](../skiphow/references/diagnosis.md) to reproduce the original failure signal with the fastest loop you can build and to test the proposed cause against it. A diagnosis-only request ends here with the cause, how you showed it, and the fix you would make.

## Fix the cause

Name the rule that failed. Find the other paths that rely on it, and the other places the owner would see the same symptom, because one symptom can have a second cause. Fix the layer that owns the rule once, with no guard, check, or special case per place. A general fix needs no repository-wide refactor, and a separate problem found on the way is a finding under the kernel's Engineering standard.

Open [technical design](../skiphow/references/technical-design.md) when the fix depends on outside facts, adds a dependency or abstraction, or could reuse something the project already has.

## Prove it

Show that the original failure is gone on the real failing path and that the fix holds on the sibling paths, not only for the reported inputs. A regression test follows [testing](../skiphow/references/testing.md#regression-tests). Then review the change and complete the authorized delivery. If you cannot establish the cause or reach the real failing path, say so instead of calling a theory verified.

Report the cause, the reach of the fix, how you checked the original and sibling cases, and the delivered state or the remaining blocker.
