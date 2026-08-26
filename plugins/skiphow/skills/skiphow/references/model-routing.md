# Model routing

The root agent runs on the model the owner chose for the session. Delegates get the model their job needs. Shared policy names roles and tiers, never a provider's model IDs; host adapters resolve them.

## Three roles

| Role | Tier | Work | Boundary |
| --- | --- | --- | --- |
| `scout` | `FAST` | Bounded search, inventory, duplicate checks, log and test-output extraction, fact checks with a direct answer | Read-only |
| `builder` | `STANDARD` | Implementation, tests, and docs for one owned scope | Isolated worktree, no remote writes |
| `reviewer` | `DEEP` | Planning an epic, unknown causes, architecture, security, build-versus-reuse judgment, independent review | Read-only plus running checks |

Mutation starts at `STANDARD`. Use `scout` only when the answer is narrow and easy to check; a cheap model on an ambiguous task spends more turns than it saves in tokens. Use `reviewer` for security changes, public contracts, large integrations, weak verification, or a repeated failure; ordinary changes need self-review and tests, not a panel.

## Delegate deliberately

Delegate only when isolation or parallelism pays for the transfer. Work that fits the current context stays in it. Every delegation names its role; nothing inherits by omission. Give the delegate a brief (objective, inputs, owned scope, what to return) and accept a summary back, never a transcript. Delegates never hold credentials or perform remote writes.

After a second failure with the same cause, raise the role one tier or review the premise. After one more failure, stop and report `BLOCKED`.

## Hosts

Claude Code: the plugin ships `scout`, `builder`, and `reviewer` under `agents/`; invoke them as `skiphow:<role>`. The reviewer runs on the session model, so escalation ends at the model the owner chose. If the host substitutes a model, treat the route as inherited and say so.

Codex: there are no family aliases and plugins cannot ship agents, so every delegate runs on the session model; the tiers collapse to role, sandbox, and reasoning effort on that one model. When the owner asks for routing, copy the three files from this skill's `codex-agents/` directory into `.codex/agents/` (read-only `scout` at low effort, workspace-write `builder`, read-only `reviewer` at high effort, `model` unset) and spawn them by name. Without them, delegates inherit the parent's effort and sandbox too.

Record the effective model when the host reports it. Cost or speed claims stay `UNVERIFIED` until paired runs show them.
