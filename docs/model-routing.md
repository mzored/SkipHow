# Model routing

SkipHow chooses a model by the work it must do. Shared policy never names a provider model or keeps a model catalog. The host resolves the current model, availability, and account limits.

This policy separates four decisions:

- the work role, such as researcher, implementer, integrator, or reviewer;
- the execution shape, such as the current session or an independent subagent;
- the capability tier;
- the reasoning effort.

A long task does not require the strongest model for every step. A short security decision may.

## Capability tiers

| Tier | Use |
| --- | --- |
| `FAST` | Bounded read-only search, inventory, extraction, and fact checks with direct verification |
| `STANDARD` | Implementation, debugging, tests, and documentation |
| `DEEP` | Product shaping, architecture, security, unknown causes, build-versus-reuse decisions, integration across contracts or systems, and risk-based independent review |

The root agent and final integrator inherit the model selected by the owner or host. For an independent subagent, the root maps a tier only from current capability, cost, or latency metadata exposed by the host, then selects the concrete route at spawn. It does not infer capability or price from a model name. If the host exposes no trustworthy mapping or no per-agent choice, the subagent uses `inherit` and model selection remains `UNVERIFIED`. Model choice never expands a worker's authority. The root retains external mutations and protected actions.

`FAST` does not receive normal code mutation by default. A cheap but plausible code change can cost more after repair, review, and context transfer than starting with `STANDARD`.

## Route and escalation

SkipHow derives the route from the task and repository. It does not ask the owner to choose a model, fill out a risk form, or pay for a separate router call.

Use these rules:

- retry a transient provider error on the same route;
- fall back to a compatible host choice, then `inherit`, when a requested capability is unavailable;
- allow one corrective attempt after a meaningful verification failure;
- raise reasoning effort or move up one tier after repeated reasoning failure or new material risk, counting promotion only when the effective route changes;
- keep a mutable lane on one tier while it owns a branch or worktree;
- downgrade only for new independent work or a bounded follow-up;
- use independent `DEEP` review for security, public contracts, large integrations, weak verification, or a repeated failure.

Treat authentication, data boundaries, and public-contract changes as material integration. An escalation checkpoint preserves the owner outcome, constraints, current state, evidence, and unresolved findings. After a same-tier correction and one promoted or independently reviewed attempt fail without a changed premise, record `BLOCKED` instead of looping.

## Cost and evidence

Measure the cost of the checked result. Include the root session, subagents, copied context, retries, review, and failed attempts. Price per model call is not the outcome cost.

Repository tests can verify that the skill contains no stale model IDs and that routing rules load. They cannot prove that a host chose the intended model or that the route saved money.

Claims about quality or savings need paired live runs on the same tasks. Compare an operator-controlled adaptive map with an all-`DEEP` baseline, keep reasoning-effort rules equal, run several trials, and grade the final state independently. That comparison can measure the recorded routes; it cannot prove that installed SkipHow chose them autonomously. Both claims remain separate and `UNVERIFIED` until exact host telemetry supports them.

The [model-routing research](research/2026-08-25/model-routing.md) records the evidence behind this policy. [ADR 0003](decisions/0003-semantic-model-routing.md) records the decision.
