# Model routing

The root agent runs on the model the owner chose for the session. Delegates get the model their job needs. Shared policy names roles and tiers, never a provider's model IDs; host adapters resolve them.

## Three roles

| Role | Tier | Work | Boundary |
| --- | --- | --- | --- |
| `scout` | `FAST` | Bounded search, inventory, duplicate checks, log and test-output extraction, fact checks with a direct answer | Read-only |
| `builder` | `STANDARD` | Implementation, tests, and docs for one owned scope | Isolated worktree, no remote writes |
| `reviewer` | `DEEP` | Planning an epic, unknown causes, architecture, security, build-versus-reuse judgment, independent review | Read-only plus running checks |

Mutation starts at `STANDARD`. Use `scout` only when the answer is narrow and easy to check; a cheap model on an ambiguous task spends more turns than it saves in tokens. Every project change closes with a `reviewer` pass; security changes, public contracts, large integrations, weak verification, or a repeated failure also send the work there earlier.

## Delegate deliberately

Delegate only when isolation or parallelism pays for the transfer; work that fits the current context stays in it. The root carries the role naming, the brief, and the escalation; this reference adds only the tier.

## Hosts

Claude Code: the plugin ships `scout`, `builder`, and `reviewer` under `agents/`; invoke them as `skiphow:<role>`. The reviewer runs on the session model. If the host substitutes a model, treat the route as inherited and say so.

Codex: plugins cannot ship agents and there are no family aliases, so every delegate runs on the session model and the tiers collapse to reasoning effort on it. Spawn with `fork_turns="none"`, the brief as the message, and `reasoning_effort` `low` for `scout` and `high` for `reviewer`; `builder` keeps the session's. A full-history fork ignores the override. Delegates share the session sandbox, so the brief states what the delegate must not change.

## The other host reviews the candidate

Both paths above run the reviewer on the session model, so it carries the priors of the run that wrote the change. When the review widens (see [engineering methods](engineering.md)), send that one pass to the other host instead — not a stronger tier, a different one. Escalation ends there. It covers a candidate change only, with no model named: the tool's own default answers. Ask for the `DEEP` level only where the host validates it.

The other host is available when its command resolves and a bounded auth check answers. Brief it with the exact candidate, say the reviewer is external, and ask for findings only; a skill installed there may still engage, so treat a reply that is not findings as a dropped pass.

- From Claude Code: `codex review --strict-config -c sandbox_mode="read-only" -`, brief on stdin; its scope flags exclude a brief, so the brief carries the range.
- From Codex: `claude -p - --effort high --permission-mode plan`, brief on stdin; plan mode bounds the model's tools, not the reviewed repository's own hooks.

Treat the verdict as the in-host reviewer's. When the other host is absent or fails, the in-host `reviewer` takes the pass and Limits says the independent pass shared the session's model. Nothing is configured: availability is the switch, and the pass runs a tool the owner already installed, on this machine, under the authority the change already carries. The report names which host judged.

Record the effective model and effort the host reports. Cost or speed claims stay `UNVERIFIED` until paired runs show them.
