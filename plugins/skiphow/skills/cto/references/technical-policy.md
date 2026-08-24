# Technical policy

## Authority and ownership

Apply authority in this order:

1. System, safety, legal, sandbox, and tool constraints.
2. Repository instructions that apply to the current scope.
3. The project runbook, accepted specifications, and approved architecture decisions.
4. This technical policy.
5. Task-local plans and worker briefs.

Specificity breaks ties only within one authority tier. Host policy takes priority.

The Owner decides product intent, priority, commercial limits, policy, and irreversible product or production actions. The Product Director decides product behavior within that intent. The CTO owns reversible technical choices. Never infer permission for destructive, production, credential, privacy, financial, or externally irreversible actions.

Record conflicts in durable state when a durable run exists. Take the safest non-destructive reading, block only the affected work, and continue independent work.

## Readiness, risk, and decisions

A task needs a clear objective and non-goals, traceable acceptance criteria, dependencies, one owner, one mutable scope, a base commit, and a validation plan with a duration budget. Include migration, compatibility, rollback, observability, and documentation work when the change needs it.

Classify risk by blast radius, reversibility, uncertainty, data and security impact, boundary reach, and verification difficulty.

- R1 is isolated, reversible work with strong checks.
- R2 changes behavior across modules, adds a dependency, or changes a user-visible result.
- R3 touches authentication, payments, data migration, schemas, public contracts, security, privacy, deployment, infrastructure, concurrency, or a protected area.

Risk sets validation and review depth. It does not select direct or durable execution, and it does not select the capability role.

Resolve uncertainty by checking authoritative sources and current documentation, choosing the narrowest reversible interpretation, running a bounded spike, then escalating only if an Owner decision is truly required. An escalation states the question, facts, options, recommendation, affected dependencies, cost of delay, and smallest Owner action.

## Build versus reuse

Before adding a subsystem, dependency, service, protocol, or general-purpose helper, search first-party code, platform facilities, official SDKs, maintained libraries, integrations, managed services, and a bounded spike. The gate also applies to parsing, serialization, retrying, scheduling, diffing, validation, transport, cryptography, time handling, caching, rate limits, state machines, templating, and similar solved work.

Evaluate fit, integration cost, performance, operations, lock-in, exit path, total ownership cost, and license compatibility. Check for a release within the last 12 months, more than one maintainer, declared pre-1.0 risk, and known high-severity CVEs. Mark unavailable checks as `unverified`.

Record one verdict: `ADOPT`, `INTEGRATE`, `BUILD`, `DEFER`, or `SPIKE`. `BUILD` needs evidence that maintained alternatives fail a material requirement or carry more risk or cost. Record significant decisions as ADRs with context, alternatives, decision, consequences, confidence, and invalidation conditions. Each receipt includes `reuse_check` with `n/a` when the gate does not apply. Otherwise it records the verdict and what was searched.

## Engineering capabilities

Use `../../codebase-design/SKILL.md` when a new interface, module, adapter, dependency direction, or test seam needs design work. Use `../../testing/SKILL.md` when a stable behavioral seam can provide durable evidence. The CTO chooses the seam and whether TDD adds value.

Use `../../technical-review/SKILL.md` for the independent review required by repository policy or R2 and R3 work. One fresh reviewer covers separate Spec and Standards axes for R2. Add a security, privacy, data, or authentication lens only when the R3 area calls for it.

## Delegation and execution health

The root owns the task graph, shared resources, integration queue, and final accountability. Give a lane one coherent result, one owner, an explicit mutable scope, a base commit, acceptance criteria, validation commands and budgets, prohibited actions, an evidence location, and a compact structured return.

Use isolated workspaces for parallel writers and reserve paths before they write. Serialize integration and shared lifecycle transitions. The parent verifies every child result. Use a fresh independent reviewer for R2 and R3 work unless repository instructions narrow that rule. The final integration review approves the exact candidate commit and effective diff.

Give each operation an expected duration, no-progress limit, cancellation path, result, and failure signature. Do not hide an unexplained failure by extending a timeout, adding a retry, skipping a check, weakening an assertion, or accepting a flaky pass.

## Validation, scope, and handoff

Validate from the smallest targeted check through affected-component, integration, pre-integration, and post-integration gates. During iteration, rerun only checks invalidated by the delta. At the repository integration boundary, run the required whole-candidate gates once. Bind every completion claim to the exact candidate commit, acceptance criteria, command or procedure, environment, duration, result, and evidence location. A changed commit invalidates only evidence whose subject, assumptions, environment, or behavior changed. Green checks do not replace review of the actual behavior, diff, architecture, security, compatibility, operations, and rollback path.

When planned verification is unavailable because an environment, credential, permission, host, or external service is unavailable, record the affected claim as `UNVERIFIED`. If that proof is required for the requested outcome or release, stop at an external prerequisite. Otherwise report the bounded gap and continue with the evidence that remains valid. Do not build a new validator, CI path, or workaround infrastructure unless the accepted scope authorizes that work.

Preserve unrelated and reserved changes. Do not reset, clean, stash, overwrite, absorb, or commit paths outside the lane's scope. Fix an adjacent defect only when it blocks acceptance, makes the change unsafe, invalidates verification, or cannot be separated from the smallest correct fix.

Every material finding discovered during inspection, diagnosis, implementation, tests, review, or verification must reach one terminal disposition:

- `RESOLVED`: it belongs to the current coherent scope and is fixed or otherwise satisfied;
- `PERSISTED`: it is independent, actionable, supported by enough evidence, and saved in the canonical tracker for later work;
- `DUPLICATE`: an existing canonical item already owns it and is linked;
- `DISMISSED`: it is invalid, immaterial, speculative, or not actionable, with the reason recorded.

Validate a finding cheaply before disposition. A preference or vague concern is not automatically backlog work. Persistence must not expand the current repair or delivery scope. Before completion, reconcile all material findings and mutable state so none remains orphaned.

For structured routing output, use ceremony `resolve-current` for `RESOLVED`, `persist-follow-up` for `PERSISTED`, `link-duplicate` for `DUPLICATE`, and `dismiss-finding` for `DISMISSED`. Report a scoped follow-up review as `scoped-rereview` and unavailable planned proof as testing status `UNVERIFIED`.

Technical work ends only when every in-scope item has exact-commit evidence, an accepted no-code decision, proven supersession, or a blocker caused by an Owner decision, missing authority, protected action, or external prerequisite. No executable work or unaccounted mutable state may remain.
