# Codebase design

Design for a small interface that hides meaningful behavior and concentrates future change. Inspect callers, dependencies, invariants, failure modes, and existing architectural decisions before proposing a new seam.

Judge the design by what callers must know. Prefer fewer concepts and parameters when the module can own the complexity. Use the deletion test: if removing the module merely deletes indirection, it is too shallow; if its complexity would spread across callers, it is earning its place.

Introduce a seam when behavior truly varies, a system boundary requires an adapter, or testing needs a stable interface. Do not add hypothetical layers for one implementation. Pass external dependencies in and expose observable results instead of internal state.

When the choice is consequential, compare genuinely different designs against the same constraints. Consider caller simplicity, locality of change, failure handling, migration cost, and testability. Recommend the strongest option. Keep the comparison technical unless a trade-off changes visible product behavior, cost, risk, or rollout.

When the requested outcome authorizes project changes, implement only the design needed by that outcome and preserve project conventions. Record a durable decision only when the owner asked to save it or the authorized project change normally includes decisions of this weight. For design-only work, report the recommendation without changing the project.
