---
name: skiphow
description: Route owner requests to idea capture, product shaping, diagnosis, or delivery while keeping product and technical decisions away from the owner when specialists can resolve them.
---

# skiphow

Treat the human as the Owner. Route the request, then let the owning workflow do the work. Do not add ceremony to a simple informational question.

## Route the intent

- Capture a thought without analysis with `idea`.
- Explore whether or how the product should change with `shape`.
- Investigate broken, failing, throwing, or slow behavior with `diagnose`.
- Start approved product work with `develop`.
- Send dependency updates, refactors, CI work, and other technical maintenance directly to technical execution. Use `cto-run` only when the work needs an orchestrated campaign.
- Answer ordinary questions and bounded research directly.

Continue a chain when the Owner's next message changes the state. An approval such as "do it" after shaping routes to `develop`. A bug diagnosis that includes authorization to fix continues through technical verification.

## Keep the authority boundary

Route questions to the lowest role that owns the decision:

1. Specialists supply evidence and scoped work.
2. The Product Director owns user behavior, scope, priority, and success.
3. The CTO owns architecture, libraries, implementation, tests, sequencing, and integration.
4. The Owner decides only vision, material product trade-offs, scope or priority changes, cost or risk commitments, protected actions, and irreversible external actions.

Do not relay a question to the Owner when the Product Director, CTO, repository evidence, or a specialist can resolve it. When escalation is necessary, present one recommendation, the evidence, the consequence of waiting, and the exact Owner decision needed.
