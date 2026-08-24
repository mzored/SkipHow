---
name: skiphow
description: Route owner requests to idea capture, product shaping, adaptive defect repair, or delivery while keeping product and technical decisions away from the owner when specialists can resolve them.
---

# skiphow

Treat the human as the Owner. Route the request, then let the owning workflow do the work. Do not add ceremony to a simple informational question.

## Route the intent

- Capture a thought without analysis with `idea`.
- Explore whether or how the product should change with `shape`.
- Repair broken, failing, throwing, or slow behavior with `fix`. Let `fix` invoke diagnosis only when the cause is unclear.
- Start approved product work with `develop`.
- Route first-run, tracked-delivery prerequisite, GitHub Project schema, hook, or host-command readiness requests to `preflight`.
- Send dependency updates, refactors, CI work, and other technical maintenance to the internal `cto` controller. It selects direct, tracked-direct, or `cto-run`. Use `cto-run` only for a durable campaign.
- Answer ordinary questions and bounded research directly.

Continue a chain when the Owner's next message changes the state. An approval such as "do it" after shaping routes to `develop`. A defect report routes to `fix`, which owns diagnosis, repair, and proportional verification.

Product acceptance is an internal Product Director phase, not a public skill. After the CTO verifies a user-visible Product Contract at an exact candidate commit, it invokes `shape/references/product-acceptance.md`. An acceptance mismatch returns to the CTO with the concrete contract mismatch. A desired contract change returns to `shape`.

## Keep the authority boundary

Route questions to the lowest role that owns the decision:

1. Specialists supply evidence and scoped work.
2. The Product Director owns user behavior, scope, priority, and success.
3. The CTO owns architecture, libraries, implementation, tests, sequencing, and integration.
4. The Owner decides only vision, material product trade-offs, scope or priority changes, cost or risk commitments, protected actions, and irreversible external actions.

Do not relay a question to the Owner when the Product Director, CTO, repository evidence, or a specialist can resolve it. When escalation is necessary, present one recommendation, the evidence, the consequence of waiting, and the exact Owner decision needed.
