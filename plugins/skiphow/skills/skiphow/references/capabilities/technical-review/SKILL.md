---
name: technical-review
description: Internal independent review capability for CTO delivery, separating conformance from specification fit.
---

# technical-review

Use this capability only at a CTO-selected review gate. It is internal and must not create an Owner checkpoint or ask the Owner to supply technical review inputs. Resolve the delivered-state identity, effective diff, accepted specification, and repository standards from available evidence. Escalate only for a genuine product or protected-action decision under repository policy.

Assign one fresh reviewer with no implementation history when independent review is required. That reviewer reports two explicitly separate axes:

- The Spec axis checks for missing, partial, incorrect, or unrequested behavior against the accepted specification.
- The Standards axis checks departures from repository standards and relevant design problems. Documented standards take priority.

Add a conditional security, privacy, data, authorization, compatibility, operations, or other specialist lens only when the changed surface makes it relevant. Name the lens and the evidence examined.

Review the delivered state and its effective diff. Findings identify the file or behavior, evidence, severity, and required disposition. A clean review is evidence, not a replacement for required validation.

The first independent review examines the full relevant integration diff. After the CTO fixes findings, re-review only the original findings, their fix diff, and regressions plausibly introduced by those fixes. Do not restart review of untouched code or reopen settled observations. Route a new independent observation through the shared finding lifecycle without silently expanding the review loop.

Require a new full integration review only when the fix materially changes architecture, accepted scope, product behavior, a protected surface, or enough of the effective diff that the prior verdict no longer applies. Record which prior review evidence remains valid and what the delta invalidated.

Read `upstream/SKILL.md` for the pinned two-axis method. This wrapper, repository policy, and CTO decisions take precedence. In particular, use one fresh reviewer rather than the upstream two-reviewer pattern.
