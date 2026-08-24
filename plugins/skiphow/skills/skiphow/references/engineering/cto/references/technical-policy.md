# Technical policy

## Authority and ownership

Apply authority in this order:

1. System, safety, legal, sandbox, and tool constraints.
2. Repository instructions that apply to the current scope.
3. The project runbook, accepted specifications, and approved architecture decisions.
4. This technical policy.
5. Task-local plans and worker briefs.

Specificity breaks ties only within one authority tier. Host policy takes priority.

The Owner decides vision, audience, portfolio or business priority, material scope, commercial limits, cost or risk commitments, protected actions, and irreversible product or production actions. The product controller decides routine reversible behavior within that direction and may recommend priority. The CTO owns reversible technical choices. Reviewers supply evidence without taking decision authority. Never infer permission for destructive, production, credential, privacy, financial, or externally irreversible actions.

Record conflicts in durable state when a durable run exists. Take the safest non-destructive reading, block only the affected work, and continue independent work.

## Readiness, surfaces, and decisions

A task needs a clear objective and non-goals, traceable acceptance criteria, dependencies, one owner, one mutable scope, a starting-state identity, and a validation plan. Include migration, compatibility, rollback, observability, and documentation work when the change needs it.

Identify concrete changed surfaces instead of assigning a universal low, medium, or high score. Relevant surfaces include:

- authentication, authorization, permissions, security, and privacy;
- persisted data and migrations;
- billing, payments, and money;
- public APIs, protocols, and schemas;
- production infrastructure and availability;
- concurrency and shared framework primitives with a large blast radius;
- protected or irreversible external actions.

Blast radius, reversibility, uncertainty, and verification difficulty refine the evidence required for those surfaces. They do not select `EXECUTE` or `CAMPAIGN`, a tracker, or a capability role. Repository policy owns any mandatory gates.

Resolve uncertainty by checking authoritative sources and current documentation, choosing the narrowest reversible interpretation, running a bounded spike, then escalating only if an Owner decision is truly required. An escalation states the question, facts, options, recommendation, affected dependencies, cost of delay, and smallest Owner action.

Consume an existing domain glossary, context map, and ADRs automatically when they apply. Update domain vocabulary only when the work establishes or changes a durable domain concept; keep implementation detail, plans, and scratch notes out of the glossary. Record an ADR only when a decision is consequential, hard to reverse, surprising without its context, and the result of a real trade-off. Ordinary features, routine reuse choices, and architecture reviews do not create documentation by default.

## Build versus reuse

Before adding a subsystem, dependency, service, protocol, or general-purpose helper, search first-party code, platform facilities, official SDKs, maintained libraries, integrations, managed services, and a bounded spike. The gate also applies to parsing, serialization, retrying, scheduling, diffing, validation, transport, cryptography, time handling, caching, rate limits, state machines, templating, and similar solved work.

Evaluate material fit, compatibility, integration cost, security, license, performance, operations, maintenance evidence appropriate to the project's maturity, adoption or operational evidence when relevant, lock-in, exit path, and total ownership cost. Treat release cadence, maintainer count, and pre-1.0 status as context rather than universal thresholds. Repository policy may set numeric freshness or support requirements. Mark unavailable material checks as `unverified`.

When the work actually makes a dependency or subsystem decision, record one verdict: `ADOPT`, `INTEGRATE`, `BUILD`, `DEFER`, or `SPIKE`. `BUILD` needs evidence that suitable maintained alternatives fail a material requirement or cost more to own. When the ADR threshold above is met, record context, alternatives, decision, consequences, confidence, and invalidation conditions. Do not add `reuse_check` to work that made no reuse decision.

## Engineering capabilities

Use `../../../capabilities/codebase-design/SKILL.md` when a new interface, module, adapter, dependency direction, or test seam needs design work. Use `../../../capabilities/testing/SKILL.md` when a stable behavioral seam can provide durable evidence. The CTO chooses the seam and whether TDD adds value.

Use `../../../capabilities/technical-review/SKILL.md` when repository policy or a changed surface requires independent review. One fresh reviewer can cover separate Spec and Standards axes. Add a security, privacy, data, authorization, compatibility, operations, or other specialist lens only when the changed surface calls for it.

Use `../../../capabilities/prototype/SKILL.md` when one unresolved desired interaction or state-model question benefits from a disposable artifact. Return its validated decision to normal execution; do not harden or merge the prototype. Use `../../../capabilities/resolving-merge-conflicts/SKILL.md` only for an already-conflicted Git merge or rebase.

## Human-action handoff

When a credential, dashboard, account, protected environment, migration, or other step genuinely requires a person, first automate every safe authorized part that the available tools can perform. For the irreducible human action, provide the shortest precise sequence: destination, exact action, values produced or changed, secret-handling boundary, reversibility, and the signal that proves completion. Generate a helper only when it materially reduces repeated manual work; do not require a script for a short one-off procedure.

Stop before any protected or irreversible action that lacks authority. After the human reports completion, verify the resulting state from primary evidence and continue automatically. A handoff is an execution mechanism for a real prerequisite, not a reason to delegate an available agent action or ask the Owner an engineering question.

## Delegation and execution health

The root owns the task graph, shared resources, integration queue, and final accountability. Use one agent for a small coherent task. Use a read-only subagent to isolate a large investigation or documentation scan, a fresh agent for required independent review, and parallel writers only for genuinely independent mutable scopes. Delegation is a context and coordination tool, not a default rigor step.

Give any lane one coherent result, one owner, an explicit mutable scope, a starting-state identity, acceptance criteria, validation commands and budgets, prohibited actions, an evidence location, and a compact structured return. Use isolated workspaces for parallel writers and reserve paths before they write. Serialize integration and shared lifecycle transitions. The parent verifies every child result. A required final integration review covers the delivered state and effective diff.

Give each operation an expected duration, no-progress limit, cancellation path, result, and failure signature. Do not hide an unexplained failure by extending a timeout, adding a retry, skipping a check, weakening an assertion, or accepting a flaky pass.

## Validation, scope, and handoff

Validate from the smallest targeted check through any affected-component, integration, and repository-required gates. During iteration, rerun only checks invalidated by the delta. Run a required whole-state gate once at the final integration boundary. Bind every completion claim to the delivered-state identity, acceptance criteria, command or procedure, environment, result, and evidence location. The identity may be a Git commit, working tree, deployment, or generated artifact. A new identity invalidates only evidence whose subject, assumptions, environment, or behavior materially changed. Green checks do not replace review of the actual behavior, diff, architecture, security, compatibility, operations, and rollback path.

When planned verification is unavailable because an environment, credential, permission, host, or external service is unavailable, record the affected claim as `UNVERIFIED`. If that proof is required for the requested outcome or release, stop at an external prerequisite. Otherwise report the bounded gap and continue with the evidence that remains valid. Do not build a new validator, CI path, or workaround infrastructure unless the accepted scope authorizes that work.

Preserve unrelated and reserved changes. Do not reset, clean, stash, overwrite, absorb, or commit paths outside the lane's scope. Fix an adjacent defect only when it blocks acceptance, makes the change unsafe, invalidates verification, or cannot be separated from the smallest correct fix.

Every material finding discovered during inspection, diagnosis, implementation, tests, review, or verification must reach one terminal disposition:

- `RESOLVED`: it belongs to the current coherent scope and is fixed or otherwise satisfied;
- `PERSISTED`: it is independent, actionable, supported by enough evidence, and saved through the owning durable tracker adapter for later work;
- `DUPLICATE`: an existing canonical item already owns it and is linked;
- `DISMISSED`: it is invalid, immaterial, speculative, or not actionable, with the reason recorded.

Validate a finding cheaply before disposition. A preference or vague concern is not automatically backlog work. Decide `PERSISTED` before loading a tracker capability, then search for a duplicate and persist or link the finding. The adapter does not decide scope, methods, review, or orchestration. Persistence must not expand the current repair or delivery scope. Before completion, reconcile all material findings and mutable state so none remains orphaned.

For structured routing output, use ceremony `resolve-current` for `RESOLVED`, `persist-follow-up` for `PERSISTED`, `link-duplicate` for `DUPLICATE`, and `dismiss-finding` for `DISMISSED`. Report a scoped follow-up review as `scoped-rereview` and unavailable planned proof as testing status `UNVERIFIED`.

Technical work ends only when every in-scope item has final-state evidence, an accepted no-code decision, proven supersession, or a blocker caused by an Owner decision, missing authority, protected action, or external prerequisite. If coordination, evidence machinery, or meta-work starts growing faster than progress toward the requested outcome, reassess the scope and execution shape. No executable work or unaccounted mutable state may remain.
