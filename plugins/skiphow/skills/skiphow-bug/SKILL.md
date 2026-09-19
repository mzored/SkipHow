---
name: skiphow-bug
description: Investigate and repair a reported defect at its root cause, covering the general case and affected sibling paths. Use for bug fixes and recurring failures; keep diagnosis-only requests read-only.
---

# SkipHow bug

Resolve the reported defect and the class of failure that caused it. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. It governs authority, scope, delegation, review, and delivery throughout this workflow.

Use [diagnosis](../skiphow/references/diagnosis.md) to establish the original failure signal and test the proposed cause. Identify the rule that failed and inspect the sibling paths governed by it, and the other places the owner would see the same symptom, since a repeat of one symptom can have a second cause. Repair the layer that owns that rule within the authorized scope. A general repair does not require a repository-wide refactor; a separable problem takes the kernel's disposition for a problem you find.

Consult [technical design](../skiphow/references/technical-design.md) when the repair depends on external facts, introduces a dependency or abstraction, or could reuse an existing capability. Research the uncertainty that affects the repair.

Use [verification](../skiphow/references/verification.md) to prove the original failure is resolved and the rule holds beyond the reported inputs. Review the final change and complete the authorized delivery. When evidence cannot establish the cause or cover the real failing path, report that limitation rather than calling a theory verified.

Report the cause, the reach of the repair, the evidence for the original and general cases, and the delivered state or remaining blocker.
