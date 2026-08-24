# Capability routing

Resolve runtime capabilities through the host configuration. Select a capability role for every delegated packet. The role follows the work in the packet, not the task risk class.

| Role | Use for |
| --- | --- |
| `MECHANICAL` | Deterministic commands, named extraction, inventory, formatting, and bounded read-only research that returns facts. |
| `IMPLEMENTATION` | Scoped changes, ordinary debugging, test analysis, a lane owner, corpus synthesis, and per-lane review. |
| `CTO_REVIEW` | Root orchestration, an architecture or build-versus-reuse decision, an anomaly that recurs after a fix, and the one independent integration review. |

Risk class chooses review depth and validation depth. An R3 implementation can use `IMPLEMENTATION`; it needs stronger gates and an independent review. Do not raise a role merely because the repository is large.

The root selects the capability explicitly and records the actual capability used. A missing requested capability blocks only the decision or lane that needs it. Continue independent work.

Create a new lane only for an independent, bounded result. Keep one writer per overlapping mutable scope. Read-only helpers can work in parallel and return concise evidence. A direct lane can use one read-only helper. A read-only helper cannot create descendants. The parent launches reviews and verifies results. An implementer never reviews its own integration candidate.

Every worker brief names the objective, authoritative inputs, non-scope, owned paths, base commit, acceptance criteria, validation commands and budgets, prohibited actions, durable artifact location, return format, and return size limit. The return states status, exact commits, changes, evidence locations, risks, blocker, and one next action. Do not paste raw logs, diffs, transcripts, or bulk corpus text into a return.
