---
name: skiphow
description: Route owner requests to setup, idea capture, product shaping, diagnosis, repair, or delivery while keeping product and technical decisions with the roles that own them.
---

# skiphow

Treat the human as the Owner. Route the request, then let the owning workflow do the work. Do not add ceremony to a simple informational question.

## Route the intent

- Capture a thought without analysis with `idea`.
- Explore whether or how the product should change with `shape`.
- Diagnose broken, failing, throwing, or slow behavior without changing it with `diagnose` when the Owner asks only for a cause or analysis.
- Repair broken behavior with `fix`. Let `fix` invoke diagnosis only when the cause is unclear, then continue into execution.
- Start approved product work with `develop`.
- Route requests to configure or repair the standard GitHub work surface to `setup`. Route read-only first-run, tracked-delivery prerequisite, Project, hook, or host-command readiness checks to `preflight`.
- Send dependency updates, refactors, CI work, and other technical maintenance to the internal `cto` controller. Its normal path is `EXECUTE`; it uses `DIAGNOSE` for unknown causes and `cto-run` only for a durable `CAMPAIGN`.
- Answer ordinary questions and bounded research directly.

Continue a chain when the Owner's next message changes the state. An approval such as "do it" after shaping routes to `develop`. A defect report routes to `fix`, which owns diagnosis, repair, and proportional verification.

Product acceptance is a SkipHow implementation of the authority and intent check, not a universal engineering phase or public skill. Invoke `shape/references/product-acceptance.md` only when user-facing semantics changed under a Product Contract. Preserve acceptance for behavior-preserving later deltas. An acceptance mismatch returns to the CTO with the concrete contract mismatch. A desired contract change returns to `shape`.

## Keep the authority boundary

Route questions to the lowest role that owns the decision:

1. Specialists supply evidence and scoped work.
2. The Product Director owns user behavior, scope, priority, and success.
3. The CTO owns architecture, libraries, implementation, tests, sequencing, and integration.
4. The Owner decides only vision, material product trade-offs, scope or priority changes, cost or risk commitments, protected actions, and irreversible external actions.

Do not relay a question to the Owner when the Product Director, CTO, repository evidence, or a specialist can resolve it. When escalation is necessary, present one recommendation, the evidence, the consequence of waiting, and the exact Owner decision needed.
