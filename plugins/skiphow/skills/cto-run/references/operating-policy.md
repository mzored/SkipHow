# Operating policy

## Authority and ownership

Apply authority in this order:

1. System, safety, legal, sandbox, and tool constraints.
2. Repository instructions that apply to the current scope.
3. The project runbook, accepted specifications, and approved architecture decisions.
4. This operating policy.
5. Task-local plans and worker briefs.

Specificity breaks ties only within one authority tier. Host policy takes priority.

The product owner decides product intent, priority, commercial limits, policy, and irreversible product or production actions. The Product Director decides product behavior within that intent. The CTO owns reversible technical choices. The internal CTO controller applies this policy to every technical delivery; `cto-run` adds durable state and coordination. Never infer permission for destructive, production, credential, privacy, financial, or externally irreversible actions.

Record conflicts in durable state. Take the safest non-destructive reading, block only the affected lane, and continue independent work.

## Recovery and control loop

Before mutation, reconstruct the actual state from primary evidence. Inspect instructions, dirty paths, worktrees, refs, ancestry, exact commits, integration history, tracker state, CI, and authoritative external systems. Keep `briefing.md` as a concise, queryable map of the authorities, their hashes, decisions, locations, and unresolved questions. Verify any briefing entry before it supports an architecture, security, or integration decision.

Persist state before handoff, an external wait, a long operation, integration, or context loss. On recovery, re-hash the policy and runbook, rebuild from durable records, compare that result with canonical systems, retain conflicting observations, and resume safely without duplicating work.

At each boundary run: observe, reconcile, assess, decide, execute or delegate, verify, review, integrate, and learn. Reassess the whole executable frontier. Do not stop after planning, a report, one task, a recoverable failure, or a temporary outage.

## Readiness, risk, and decisions

A task needs a clear objective and non-goals, traceable acceptance criteria, dependencies, one owner, one mutable scope, a base commit, and a validation plan with a duration budget. Include migration, compatibility, rollback, observability, and documentation work when the change needs it.

Classify risk by blast radius, reversibility, uncertainty, data and security impact, boundary reach, and verification difficulty.

- R1 is isolated, reversible work with strong checks.
- R2 changes behavior across modules, adds a dependency, or changes a user-visible result.
- R3 touches authentication, payments, data migration, schemas, public contracts, security, privacy, deployment, infrastructure, concurrency, or a protected surface.

Risk sets the validation and review depth. It does not select the capability role.

Resolve uncertainty by checking authoritative sources and current documentation, choosing the narrowest reversible interpretation, running a bounded spike, then escalating only if an owner decision is truly required. An escalation states the question, facts, options, recommendation, affected dependencies, cost of delay, and smallest owner action.

## Build versus reuse

Before adding a subsystem, dependency, service, protocol, or general-purpose helper, search first-party code, platform facilities, official SDKs, maintained libraries, integrations, managed services, and a bounded spike. The gate also applies to parsing, serialization, retrying, scheduling, diffing, validation, transport, cryptography, time handling, caching, rate limits, state machines, templating, and similar solved work.

Evaluate fit, integration cost, performance, operations, lock-in, exit path, total ownership cost, and license compatibility. Check for a release within the last 12 months, more than one maintainer, declared pre-1.0 risk, and known high-severity CVEs. Mark unavailable checks as `unverified`.

Record one verdict: `ADOPT`, `INTEGRATE`, `BUILD`, `DEFER`, or `SPIKE`. `BUILD` needs evidence that maintained alternatives fail a material requirement or carry more risk or cost. Record significant decisions as ADRs with context, alternatives, decision, consequences, confidence, and invalidation conditions. Each receipt includes `reuse_check` with `n/a` when the gate does not apply. Otherwise it records the verdict and what was searched.

## Delegation and execution health

The root owns the DAG, global state, leases, shared resources, integration queue, and final accountability. Give a lane one coherent result, one owner, an explicit mutable scope, a base commit, acceptance criteria, validation commands and budgets, prohibited actions, durable evidence location, and a compact structured return. A worker writes scoped receipts and evidence. Only the root changes global state.

Use isolated workspaces for parallel writers and reserve paths before they write. Serialize integration and shared lifecycle transitions. The parent verifies every child result. Use a fresh independent reviewer for R2 and R3 work unless repository instructions narrow that rule. The final integration review approves the exact candidate commit and effective diff.

Give each operation an expected duration, no-progress limit, cancellation path, result, and failure signature. Record the first successful duration as a baseline. A later result more than one and a half times that baseline, or in a slower budget class, is an anomaly. Confirm a stalled lane with two independent observations.

After three consecutive failures with the same signature, set the lane to `CIRCUIT_BROKEN`. Reopen it only through a recorded review-tier decision that names the changed condition. Pause the affected lane, capture diagnostics, classify the cause, apply the smallest systemic correction, rerun the smallest reproducer, update durable state, and continue independent lanes. Do not hide an unexplained failure by extending a timeout, adding a retry, skipping a check, weakening an assertion, or accepting a flaky pass.

## Validation, scope, and handoff

Validate from the smallest targeted check through affected-component, integration, pre-integration, and post-integration gates. Run each required gate on the exact candidate commit. Bind every completion claim to the exact candidate commit, acceptance criteria, command or procedure, environment, duration, result, and evidence location. Green checks do not replace review of the actual behavior, diff, architecture, security, compatibility, operations, and rollback path.

Preserve unrelated and reserved changes. Do not reset, clean, stash, overwrite, absorb, or commit paths outside the lane's scope. Fix an adjacent defect only when it blocks acceptance, makes the change unsafe, invalidates verification, or cannot be separated from the smallest correct fix. During an outage, continue only authorized local work, queue remote actions idempotently, and distinguish local completion from remote completion.

The run ends only when every in-scope item has exact-commit evidence, an accepted no-code decision, proven supersession, or a blocker caused by a product-owner decision, missing authority, protected action, or external prerequisite. No executable lane or unaccounted mutable state may remain. Reconcile branches, worktrees, and dirty paths from fresh evidence. Write `FINAL.md` with completed outcomes, pending external reconciliation, blocked items, evidence, residual risks, decisions, recurring failures, recommended improvements, and confirmation that no unauthorized protected action occurred.
