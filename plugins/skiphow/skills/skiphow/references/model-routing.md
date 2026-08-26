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

Delegate only when isolation or parallelism pays for the transfer. Work that fits the current context stays in it. The root skill carries the role naming, the brief, and the failure escalation; this reference adds only which tier the job needs.

## Hosts

Claude Code: the plugin ships `scout`, `builder`, and `reviewer` under `agents/`; invoke them as `skiphow:<role>`. The reviewer runs on the session model, so escalation ends at the model the owner chose. If the host substitutes a model, treat the route as inherited and say so.

Codex: plugins cannot ship agents and there are no family aliases, so every delegate runs on the session model and the tiers collapse to reasoning effort on it. Spawn with `fork_turns="none"`, the brief as the message, and `reasoning_effort` `low` for `scout` and `high` for `reviewer`; `builder` keeps the session's. A full-history fork ignores the override. Delegates share the session sandbox, so the brief states what the delegate must not change.

Record the effective model when the host reports it. Cost or speed claims stay `UNVERIFIED` until paired runs show them.
