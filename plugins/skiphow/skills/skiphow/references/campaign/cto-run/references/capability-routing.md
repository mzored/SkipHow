# Capability routing

Resolve runtime capabilities through the host configuration. Select a capability role for every delegated packet. The role follows the work in the packet, not a generic risk label.

| Role | Use for |
| --- | --- |
| `MECHANICAL` | Deterministic commands, named extraction, inventory, formatting, and bounded read-only research that returns facts. |
| `IMPLEMENTATION` | Scoped changes, ordinary debugging, test analysis, a lane owner, corpus synthesis, and per-lane review. |
| `CTO_REVIEW` | Root orchestration, an architecture or build-versus-reuse decision, an anomaly that recurs after a fix, and the one independent integration review. |

Changed surfaces choose review and validation depth. A security-sensitive implementation can use `IMPLEMENTATION`; it may need security evidence and independent review. Do not raise a role merely because the repository is large.

The root selects the capability explicitly and records the actual capability used. A missing requested capability blocks only the decision or lane that needs it. Continue independent work.

Create a new lane only for an independent coherent result. Use read-only helpers to isolate large exploration and return concise evidence, fresh agents for independent review, and parallel writers only when their mutable scopes do not overlap and parallelism materially helps. A read-only helper cannot create descendants. The parent launches reviews and verifies results. An implementer never reviews its own integration candidate.

Every worker brief names the objective, authoritative inputs, non-scope, owned paths, starting-state identity, acceptance criteria, validation commands and budgets, prohibited actions, durable artifact location, return format, and return size limit. The return states status, final-state identity, changes, evidence locations, affected surfaces, blocker, and one next action. Do not paste raw logs, diffs, transcripts, or bulk corpus text into a return.
