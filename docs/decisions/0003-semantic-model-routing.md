# ADR 0003: Route work by semantic capability

## Status

Superseded by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). The shipped contract no
longer defines model tiers, role floors, escalation counts, or provider adapters. The requirement that cost or
quality claims need appropriate comparative evidence stands.

## Date

2026-08-25

## Context

SkipHow should use cheaper or faster models when the work is narrow and easy to verify. It should also keep difficult product, architecture, security, and integration work on a model suited to that work.

Model catalogs change faster than this project. A shared skill that names current model IDs or provider tiers will become stale and will not transfer cleanly between hosts. The retired runtime made a different mistake. Its discovery path could assign the same available model to every tier, so the tier names did not prove that routing had occurred.

Four choices are related but distinct:

- what kind of work the task requires;
- whether the root agent handles it directly or delegates it;
- what capability tier the work needs;
- how much reasoning effort the selected model should use.

Research on model cascades shows that routing can reduce cost on some workloads. It does not prove that SkipHow saves money on software delivery. Transfer context, retries, review, and failed attempts all count toward the price of a verified result.

## Decision

The shared SkipHow skill uses three semantic capability tiers.

- `FAST` handles bounded read-only search, inventory, extraction, and fact checks with an objective result.
- `STANDARD` handles ordinary implementation, debugging, tests, and documentation.
- `DEEP` handles product shaping, unknown causes, architecture, security, build-versus-reuse research, integration, and independent review when risk warrants it.

The root agent and final integrator inherit the model selected for the user's session. Delegation is optional. The root agent sends work to a subagent only when context isolation or parallel work will repay the transfer cost.

The root agent classifies a task from its work packet. The packet includes the role, mutation authority, uncertainty, risk, and available verification. SkipHow does not call a separate router model.

The portable skill contains no model IDs, versioned aliases, prices, or provider names. The root maps `FAST`, `STANDARD`, and `DEEP` only from current capability, cost, or latency metadata exposed by the host, then selects the concrete route at subagent spawn. It does not infer capability or price from a name. If the host exposes no trustworthy map, cannot choose a subagent model, or substitutes the request without reporting the effective route, the agent uses `inherit` and marks model selection and any claimed benefit `UNVERIFIED`.

Capability and reasoning effort remain separate settings. A host may run a capable model at low effort for a small task or increase effort without changing models. The core policy does not treat a tier as an effort alias.

`FAST` is not the default for code changes. Normal mutation starts at `STANDARD`. A mutable task keeps its tier while it owns a worktree or branch. SkipHow may choose a lower tier for a new, independent follow-up, but it does not downgrade an active write lane halfway through the work.

Routing failures follow these rules:

- A transient provider error retries the same route within the host's normal limits.
- A missing model or unsupported setting falls back to a compatible host choice, then to `inherit`.
- One meaningful verification failure may receive a corrective attempt at the same tier.
- A repeated reasoning failure raises effort or capability by one step. Promotion counts only when the effective model or effort changes. After one correction and one effective promoted or independent review attempt fail on the same premise, the work is `BLOCKED`.
- Independent `DEEP` review is reserved for security, public contracts, large integration changes, weak verification, or a repeated failure.

SkipHow measures the cost of the verified outcome. That includes the root session, subagents, transferred context, retries, and review. Documentation and README copy must not claim token or cost savings until paired multi-trial evaluations show no material loss in outcome quality against an all-`DEEP` baseline with the same reasoning-effort rules.

## Consequences

The policy survives model renames and transfers between hosts. It also keeps routine work from acquiring a second routing call before useful work starts.

Host integrations may make different concrete choices for the same semantic tier. Some expose no trustworthy capability or cost catalog at all. Results can therefore differ by host and installed model catalog. SkipHow reports that limitation instead of presenting tier names as proof of equivalent or autonomous routing.

The conservative mutation rule may miss some savings on mechanical code changes. That is intentional until SkipHow has outcome data for those tasks.

## Rejected alternatives

### Hard-coded model IDs

This would make the shared skill stale and provider-specific. It would also confuse a commercial model name with the capability needed by the task.

### Use the strongest model for every task

This is a safe fallback, but it spends the most on search, extraction, and other bounded work where a cheaper model can be checked directly.

### Use the cheapest model unless it fails

Failure is expensive after a model has changed code, consumed context, or produced a plausible but incorrect design. SkipHow starts mutable work at `STANDARD` instead.

### Add a learned router or calibration runtime

This would restore a stateful runtime, require provider-specific measurements, and add a model call before work begins. SkipHow can revisit this only if measured routing errors justify the extra system.

### Encode reasoning effort in the tier name

Capability and effort solve different problems. Combining them would prevent hosts from choosing a capable model at low effort or raising effort without changing the model.

## Evidence

- [Model-routing research](../research/2026-08-25/model-routing.md)
- [Host-capability research](../research/2026-08-25/host-capabilities.md)
- [Repository audit](../research/2026-08-25/repository-audit.md)
- [Security and evaluation research](../research/2026-08-25/security-and-evals.md)
- [Live evaluation host contract](../research/2026-08-25/live-evaluation-hosts.md)

## Revalidation triggers

Revisit this decision when:

- a supported host can no longer express inheritance or per-agent model choice;
- paired evaluations show a material quality loss or no total-cost benefit from semantic routing;
- a new host capability can resolve semantic tiers more reliably without model IDs in the core;
- repeated task failures show that a tier definition is too broad;
- SkipHow gains a verified workload large enough to justify a learned router.
