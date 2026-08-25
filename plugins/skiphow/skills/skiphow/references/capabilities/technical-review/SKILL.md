---
name: technical-review
description: Internal independent review capability for CTO delivery, separating conformance from specification fit.
---

# technical-review

Use this capability only at a CTO-selected review gate. It is internal and must not create an Owner checkpoint or ask the Owner to supply technical review inputs. Resolve the delivered-state identity, effective diff, accepted specification, and repository standards from available evidence. Escalate only for a genuine product or protected-action decision under repository policy.

When independent review is required and the host supports it, assign one fresh reviewer with no implementation history. Otherwise follow the repository blocker or report the review limitation as `UNVERIFIED`. The reviewer keeps two axes separate:

- The Spec axis checks for missing, partial, incorrect, or unrequested behavior against the accepted specification.
- The Standards axis checks departures from repository instructions and relevant design defects. Documented repository rules take priority over general heuristics.

Add a conditional security, privacy, data, authorization, compatibility, operations, or other specialist lens only when the changed surface makes it relevant. Name the lens and the evidence examined.

Review the delivered state and effective diff, not an obsolete snapshot. Establish the comparison point, changed files, commits when relevant, the normative user request or accepted specification, and applicable repository rules before judging the change. A missing written specification limits the Spec axis but does not invent one.

Every material finding must contain:

- concrete source or evidence and the affected file, behavior, or interface;
- claim type: confirmed defect, risk, investigation, or suggestion;
- severity based on impact, not style preference;
- required disposition: `RESOLVED`, `PERSISTED`, `DUPLICATE`, or `DISMISSED`.

Call something a confirmed defect only when evidence shows incorrect behavior or a violated requirement. Label unsupported suspicion as an investigation or risk. Skip observations already enforced by deterministic tooling unless the tool missed a concrete defect. A clean review is evidence, not a substitute for tests or other required validation.

The first independent review examines the full relevant integration diff. After the CTO fixes findings, re-review only the original findings, their fix diff, and regressions plausibly introduced by those fixes. Do not restart review of untouched code or reopen settled observations. Route a new independent observation through the shared finding lifecycle without silently expanding the review loop.

Require a new full integration review only when the fix materially changes architecture, accepted scope, product behavior, a protected surface, or enough of the effective diff that the prior verdict no longer applies. Record which prior review evidence remains valid and what the delta invalidated.
