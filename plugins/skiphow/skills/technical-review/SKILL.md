---
name: technical-review
description: Internal independent review capability for CTO delivery, separating conformance from specification fit.
---

# technical-review

Use this capability only at a CTO-selected review gate. It is internal and must not create an Owner checkpoint or ask the Owner to supply technical review inputs. Resolve the candidate commit, effective diff, accepted specification, and repository standards from available evidence. Escalate only for a genuine product or protected-action decision under repository policy.

For R2 work, assign one fresh reviewer with no implementation history. That reviewer reports two explicitly separate axes:

- The Spec axis checks for missing, partial, incorrect, or unrequested behavior against the accepted specification.
- The Standards axis checks departures from repository standards and relevant design problems. Documented standards take priority.

For R3 work, add a conditional security, privacy, data, or authentication lens when the changed surface makes that lens relevant. Name the lens and the evidence examined. Do not add it mechanically when the risk classification does not touch such a surface.

Review the exact candidate commit and its effective diff. Findings identify the file or behavior, evidence, severity, and required disposition. A clean review is evidence, not a replacement for required validation.

Read `upstream/SKILL.md` for the pinned two-axis method. This wrapper, repository policy, and CTO decisions take precedence. In particular, use one fresh reviewer rather than the upstream two-reviewer pattern.
