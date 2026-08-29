# Codebase design

Design for a small interface that hides meaningful behavior and concentrates future change. Inspect callers, dependencies, invariants, failure modes, and existing architectural decisions before proposing a new seam.

Where the owner asks to improve a structure that already exists rather than to design a new one, scope the look before taking it. Weight what the project's own history keeps returning to and what the requested outcome has to touch, because a deeper module pays for itself only where more change is coming, and a survey ranging over the whole repository returns candidates nobody will act on. Do not re-argue decisions the project has already recorded, and surface a candidate that contradicts one only when the friction is real enough to reopen it. The survey itself is a read that returns the recommendation, and one record per candidate where the request authorizes records. Where the request authorizes changes, carry out what the owner's outcome names and leave the rest as records: finding more that could be improved is not what widens the work.

Judge the design by what callers must know. Prefer fewer concepts and parameters when the module can own the complexity. Use the deletion test: if removing the module merely deletes indirection, it is too shallow; if its complexity would spread across callers, it is earning its place.

Introduce a seam when behavior truly varies, a system boundary requires an adapter, or testing needs a stable interface. Do not add hypothetical layers for one implementation. Pass external dependencies in and expose observable results instead of internal state.

When the choice is consequential, compare genuinely different designs against the same constraints. Consider caller simplicity, locality of change, failure handling, migration cost, and testability. Recommend the strongest option. Keep the comparison technical unless a trade-off changes visible product behavior, cost, risk, or rollout.

When the requested outcome authorizes project changes, implement only the design needed by that outcome and preserve project conventions. Record a durable decision only when the owner asked to save it or the authorized project change normally includes decisions of this weight. For design-only work, report the recommendation without changing the project.
