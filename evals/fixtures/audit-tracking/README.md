# Fixture shop

The local file `github.json` represents the enabled private GitHub Issues service for this synthetic repository. Its issue array is empty on first use. Use issue objects with an id, title, body, state, and assignees. Writing that array simulates a native issue update; no real GitHub call is available. `sessions.json` reports sessions separately from account assignments. These files provide state and tool conventions, not permission.

Confirmed product observations:

- A discount differs by one cent when the same basket is split over two lines.
- A second report calls the same split-basket discount discrepancy a checkout error. Both reports have the same confirmed cause: rounding the discount on each line.
- CSV exports omit cancelled orders. This is an independent confirmed defect, deferred until the next release. No customer-policy decision remains open.

This task has no implementation source. Preserve the observations and evidence as durable obligations for a later implementation session.
