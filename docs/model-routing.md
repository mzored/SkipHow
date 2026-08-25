# Model routing

SkipHow routes by semantic profile, required capability, risk, and verified outcomes. Core policy never names a provider model. The provider-neutral implementation is `src/skiphow/model_routing.py`; adapters or local runtime configuration supply versioned catalog entries.

## Profiles and preferences

Core understands three profiles. Their serialized values are lowercase:

- `ECONOMY` selects the least expensive eligible capability for bounded work with strong verification.
- `BALANCED` is the normal implementation profile.
- `FRONTIER` is reserved for high-judgment work, weak verification, high error cost, and integration boundaries.

The user-facing preference is `auto`, `economy`, `balanced`, or `quality`. This preference changes the cost and quality policy. It does not bypass capability checks, mutation authority, or the configured safety floor. Concrete model identifiers, availability, context limits, pricing, and provider flags belong in adapter or advanced local configuration.

## Route inputs

The controller derives task features. It does not ask the Owner to fill out an engineering form. `schemas/route.schema.json` defines the persisted feature record, including task kind, mutation level, uncertainty, error cost, reversibility, blast radius, verification strength, context volume, parallelizability, required capabilities, latency priority, and remaining budget.

The current heuristic API uses a compact `TaskFeatures` projection. It records taxonomy, repository, read-only status, strong or weak verification, high-impact flags, expected token volume, required capabilities, and latency sensitivity. Provider integration must derive this projection from controller state rather than ask the Owner for it.

Required capabilities may include code editing, long context, vision, browsing, structured output, delegation, tool use, computer use, or local execution. The router first excludes models that lack a hard capability, required authority, enough context, acceptable availability, or the configured safety level.

For the remaining catalog entries, the heuristic weighs recent verified success for the same task taxonomy and model version, estimated token cost, latency, and context overhead. It chooses the lowest-scoring entry that clears the quality floor. `RouteDecision` records the candidate, profile, short reason, estimated cost, and calibrated success rate.

## Cold start

Before enough verified outcomes exist, routing stays conservative:

| Situation | Default profile |
| --- | --- |
| Read-only extraction with a strong verifier | `ECONOMY` |
| Ordinary implementation, tests, or bounded debugging | `BALANCED` |
| Architecture, security, protected actions, weak verification, public contracts, campaign decomposition, or final integration | `FRONTIER` |

A simple task should run on the current eligible host model when a separate routing call would cost more than it saves. SkipHow does not create a router agent merely to choose a model.

## Lanes and escalation

A mutable lane stays on its selected profile until it reaches a checkpoint or has a reason to escalate. This avoids repeated context transfer and route oscillation.

Escalation is bounded. A failed verifier, repeated no-progress signature, unexpected scope growth, material ambiguity, high-impact finding, insufficient capability or context, systemic review finding, or high-cost external side effect can promote the lane. The runner must not retry forever on the same profile. Switching models requires a checkpoint that preserves the requested outcome, constraints, current state, evidence, and unresolved findings.

Downgrade is allowed before substantive mutation, on a new independent lane, or for a mechanical follow-up with strong verification. It is not allowed halfway through an unfinished reasoning chain.

## Outcome feedback

Every routed task records the provider, model, exposed version, profile, route reason, reliable usage and cost, latency, verifier result, review findings, retries, promotions, and terminal outcome. Calibration is version-aware and gives less weight to old results. A provider or evaluator update does not inherit permanent confidence from an earlier version.

Start with simple statistics by task taxonomy and repository. Online learning or a contextual bandit needs enough execution-verified data first. Logs and calibration records must not contain credentials, raw prompts, or unredacted repository content.

## Current implementation boundary

`CampaignExecutor` passes a route decision to a provider session and records the reason and verification checkpoint. The catalog and calibration store remain in memory; durable outcome history is not wired into the runner database. Low-weight history is ignored, and exact model versions plus recency decay prevent stale results from acting as current evidence. Routing remains heuristic until durable telemetry and live release comparisons exist.

## Evaluation and acceptance

Routing evidence comes from the opt-in live suite described in [Evaluation and release evidence](evals.md). Run the same real tasks across all-`FRONTIER`, all-`BALANCED`, and adaptive routing. Use several trials and exact version receipts.

Adaptive routing passes its release gate only when it lowers cost against all-`FRONTIER` without a statistically detectable loss in terminal success and without new unauthorized mutations. The `model-routing` scenario checks that cheaper profiles preserve success. The `escalation` scenario checks that a weaker profile failure promotes once, carries a valid checkpoint, and does not oscillate.

Until that evidence exists for the current versions, routing behavior and savings remain unverified. Repository tests can validate route contracts, catalog neutrality, safety floors, bounded promotion, receipt shape, and deterministic graders. They cannot prove live model quality.
