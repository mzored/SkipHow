# Model routing research

## Record

- Reviewed on 2026-08-25.
- Repository commit: `a6d34a25614bc0723517032af617b0782158df4d`.
- Repository version: `v0.6.0-21-ga6d34a2`.
- Scope: the current Python router, host model controls, research on model cascades, and the replacement policy for the portable SkipHow skill.
- Status: the repository findings below are verified. Savings from adaptive routing remain `UNVERIFIED`.

Commands used for the repository check:

```text
git rev-parse HEAD
git describe --tags --always --dirty
python scripts/check.py --pytest -q tests/test_model_routing.py tests/test_supervisor.py -k 'routing or route or calibration'
```

The focused test run reported `15 passed, 27 deselected`. Those tests prove that the current code follows its declared routing contracts. They do not prove that it assigns suitable models or reduces the cost of real work.

## Conclusion

SkipHow should keep model routing as a small policy inside the skill. The host should select the actual model. SkipHow should not own a model catalog, router service, calibration database, or provider adapter.

The policy has three provider-neutral capability tiers named `FAST`, `STANDARD`, and `DEEP`. A tier is only one routing input. Work role, execution shape, and reasoning effort remain separate choices. This distinction matters because a long task can contain a cheap read-only inventory, while a short security decision may need the strongest available model.

Use `inherit` whenever the host cannot resolve a requested tier or does not support per-agent model selection. An inherited route is normal operation, not an error. Any claim that this policy saves money stays `UNVERIFIED` until paired real-provider evaluations support it.

## Verified facts about the implementation at the audited commit

The implementation at that commit lived in `src/skiphow/model_routing.py`, `src/skiphow/supervisor.py`, `src/skiphow/routing_runtime.py`, and the provider adapters. Those runtime files were later removed.

It gets some design choices right:

- Core routing code does not contain provider model IDs.
- Routes record model version, cost when available, verifier result, retries, and terminal outcome.
- Mutable lanes remain on one route until a checkpoint.
- Promotions have a bound.
- Repository tests do not call live models.

The implementation still cannot deliver the behavior described in `docs/model-routing.md`:

1. `route_provider_catalog` asks `route_provider_models` to build `ECONOMY`, `BALANCED`, and `FRONTIER` routes from the same discovered model list. `model_candidate` then assigns the requested profile to each model. The adapter does not establish that a discovered model belongs to that capability tier. One discovered model can therefore fill all three tiers.
2. The runtime passes a synthetic `TaskFeatures` value with taxonomy `campaign-execution`. It marks work as read-only with a strong verifier only when the requested profile is `ECONOMY`. It does not derive the documented task kind, uncertainty, security risk, public contract risk, context need, or actual verifier strength from the work item.
3. The route score can compare catalog price and recorded outcomes, but those inputs do not repair the artificial tier assignment. Calibration can make a precise choice among incorrectly labelled candidates.
4. The supervisor and SQLite store own route persistence, promotion state, and outcome calibration. This duplicates controls that current hosts already expose and couples model choice to the runner that the replacement removes.
5. The live provider adapter starts a bare Codex or Claude session in a fixture directory. It does not install and activate the exact SkipHow candidate under evaluation.
6. The synthetic `model-routing` scenario declares task-level routing outcomes, but the current concrete collectors do not observe task-level model selection. `docs/evals.md` already marks the adaptive-routing ablation and multi-trial provider evidence as `UNVERIFIED`.

These are product gaps, not missing unit tests. Adding more catalog fields or calibration math would preserve the wrong boundary.

## Four separate decisions

The controller decides each axis independently.

| Axis | Question | Examples | What it must not imply |
| --- | --- | --- | --- |
| Work role | What responsibility does this agent have? | root owner, explorer, implementer, reviewer, integrator | A reviewer does not always need `DEEP`. |
| Execution shape | How should the work run? | current session, one subagent, parallel read lanes, isolated worktree, background goal | A background goal does not make every lane expensive. |
| Capability tier | How much model capability does this task need? | `FAST`, `STANDARD`, `DEEP` | The tier does not name a provider model. |
| Reasoning effort | How much reasoning should the selected model use? | inherit, low, medium, high, or another host-supported value | Effort is not a synonym for model tier. |

The root agent and final integrator inherit the user's selected parent model unless the host already applies a stronger policy. Subagent work may request another tier when the task has a clear boundary and evidence can check its result.

## Capability tiers

### `FAST`

Use `FAST` for bounded, read-only work with a clear output and cheap validation. Suitable work includes file inventories, log extraction, source lookup, duplicate candidates, and structured fact collection.

Do not use `FAST` for ordinary code mutation, final integration, unresolved debugging, product judgment, architecture, security, or a task whose result cannot be checked without repeating the reasoning.

### `STANDARD`

Use `STANDARD` for normal implementation, testing, documentation, bounded debugging, and integration with a known design. This is the default tier for mutable work.

The task still needs a capable coding model. `STANDARD` means the normal implementation choice, not the cheapest available model.

### `DEEP`

Use `DEEP` for product shaping, architecture, security, an unknown failure cause, build-versus-reuse research, public contracts, high-cost external actions, final integration with weak verification, and an independent review after repeated failure.

Do not add a `DEEP` reviewer to every change. A targeted test and a small diff usually give stronger evidence than another expensive opinion.

## Cold start and host fallback

SkipHow should not call a router model. The root agent classifies the lane from the task packet and the rules above.

At cold start:

1. Keep the root agent and integrator on `inherit`.
2. Choose `FAST` only for bounded read-only work with a direct check.
3. Choose `STANDARD` for mutable work when no high-risk condition applies.
4. Choose `DEEP` when the work matches a listed high-judgment or high-impact condition.
5. Default an unclear low-risk classification to `STANDARD`. Default unclear high-impact work to `DEEP`.

The host maps a tier to a current model if it supports that control. Shared SkipHow instructions never store a provider name, model ID, release alias, context limit, or price.

If the host cannot honor the request, use `inherit`. Record the requested tier, effective model when the host reports it, effort, route reason, and whether the mapping was inherited. Do not guess the effective model or its price.

OpenAI's current Codex documentation confirms that subagent model and reasoning effort are separate settings. A subagent inherits both when no override exists. It also warns that subagents consume more tokens than a comparable single-agent run. This supports the fallback and the decision to delegate only when the work divides cleanly.

## Effort policy

Choose effort after choosing the model tier. Use the host's vocabulary and capability checks.

- Use `inherit` as the portable default.
- Request low effort for mechanical extraction when a verifier can reject mistakes.
- Use the host's normal effort for implementation and debugging.
- Raise effort for a hard reasoning step only when representative evaluations show a gain or the current attempt exposes a specific reasoning gap.
- Do not copy one provider's effort names into the shared skill.

The policy does not hard-code `FAST` to low effort or `DEEP` to high effort. A provider may offer a fast model that needs its default effort, while a strong model can handle a routine check at low effort.

## Escalation and retry rules

A mutable lane keeps its effective model and effort until a checkpoint. This avoids paying for repeated context transfer and stops routes from oscillating.

Handle failures by cause:

- Retry a transient transport or rate-limit failure on the same route according to the host's retry policy. Do not promote the model for an infrastructure error.
- If the selected model lacks a required tool, context size, input type, or permission, select the nearest eligible stronger tier. Use `inherit` if the host cannot make that selection.
- After the first substantive verifier failure, give the same lane one corrective attempt with the failure evidence.
- If the same failure signature repeats, save a checkpoint and promote one tier.
- If a `DEEP` lane repeats the same failure, stop blind retries. The root agent must change the approach, narrow the task, or report a real blocker.
- Promote immediately when new evidence makes the work security-sensitive, changes a public contract, raises the cost of error, or weakens verification.
- Downgrade only for a new independent lane or a mechanical follow-up. Do not downgrade midway through unfinished reasoning or mutation.

A checkpoint carries the requested outcome, hard constraints, accepted decisions, changed state, verification evidence, failure signature, unresolved findings, and exact Git state. It should not carry the full transcript.

## Cost to verified success

The useful cost metric is the total cost of reaching a verified terminal result. It includes:

- root and integrator usage;
- all subagent usage;
- context transferred between agents;
- retries and failed attempts;
- independent review;
- verifier work that incurs model cost.

Count failed runs. Otherwise a route that succeeds once after several expensive failures can look cheaper than a route that succeeds on the first attempt.

Report terminal success and unauthorized mutations before cost. Then report total tokens, provider-reported cost, latency, attempts, promotions, and review calls. If the provider does not report trustworthy usage or price, mark cost as `UNVERIFIED` rather than reconstructing it from stale constants.

RouteLLM and FrugalGPT show that routing and cascades can reduce inference cost on their studied datasets. Neither paper proves that a three-tier policy reduces the cost of autonomous software work. SkipHow must measure its own tasks.

## Paired evaluation requirement

Do not publish a cost-saving claim until the live suite compares two policies on the same versioned tasks:

- baseline with every lane assigned the `DEEP` capability tier and the same effort rules;
- adaptive routing with `FAST`, `STANDARD`, `DEEP`, and the escalation rules above.

An all-`STANDARD` or all-inherited run can help diagnose results, but neither is the main baseline.

The evaluation must:

1. Install and activate the exact candidate plugin.
2. Use the same initial fixture, user request, permissions, host version, model versions, and success rules for each pair.
3. Run several pairs in alternating or randomized order.
4. Grade final repository and service state through collectors outside the model response.
5. Record every agent's effective model, effort, usage, latency, retries, and terminal evidence when the host exposes them.
6. Include read-only research, normal code mutation, unknown debugging, high-risk review, and multi-lane work.
7. Treat unauthorized mutation, missing required evidence, or an unverified terminal state as failure.

Adaptive routing passes only when it preserves terminal success and authority compliance on representative tasks, then lowers total cost to verified success. A small run can find regressions. It cannot support a general statistical claim.

## Rejected approaches

### Custom router and calibration store

Reject the Python model catalog, heuristic scorer, sticky route database, and online calibration store. They duplicate host behavior, require volatile provider facts, add another state owner, and have no real-provider evidence. Calibration is especially tempting because it looks scientific. With weak collectors and artificial tier labels, it only gives bad inputs more decimal places.

### A model call that chooses the model

Reject a separate router agent. It adds latency, tokens, another failure mode, and another prompt to maintain. The initial policy has few categories and the root already has the task context.

### Concrete model IDs in shared policy

Reject provider names, model IDs, prices, and context limits in `SKILL.md` or shared references. Hosts change catalogs and account availability. A host-specific personal configuration may map the semantic tiers, but the core must work through `inherit` without it.

### Fixed model by job title

Reject rules such as "all researchers are cheap" or "all reviewers are strong." A researcher can make a security judgment. A reviewer can check a two-line mechanical change. Route the bounded task, not the title.

### Strongest model everywhere

Reject this as the default. It is a useful evaluation baseline, not a product policy. It wastes model work on inventory and extraction, and it can make parallel delegation far more expensive than the parent run.

### Learned router now

RouteLLM provides evidence that learned strong-versus-weak routing can work with suitable preference data. SkipHow does not have enough trusted, versioned software-task outcomes to train or validate one. Revisit only after the simple policy has a large exact-version dataset and a measured failure that a learned router could address.

## Limits and revalidation triggers

The policy cannot guarantee lower cost, shorter latency, or better quality. Host routing may hide the effective model. Provider pricing can omit tool costs or cache effects. Model updates can change the best choice without changing a public alias. Subagents also repeat context and tool work.

Revalidate this research when any of these events occurs:

- Codex or Claude changes model inheritance, per-subagent selection, effort controls, or usage receipts.
- SkipHow adds another supported host.
- A host removes tier selection and changes the meaning of `inherit`.
- A provider changes a model family, alias, pricing scheme, context behavior, or tool support.
- New work types no longer fit the tier rules.
- Paired evaluations show a terminal-success regression, repeated escalation, or no cost benefit.
- Security policy changes which work may go to a subagent.
- Context transfer or review costs become a large part of total run cost.

Revalidation should update this research and the model-routing ADR. Do not add a new runtime component merely because a source or model name changed.

## What to keep

- Provider-neutral semantic tiers.
- Conservative cold-start rules.
- Root and integrator inheritance.
- Separate model and effort choices.
- Sticky mutable lanes with checkpointed promotion.
- Exact effective-route receipts when the host supplies them.
- Cost measured across the complete verified run.
- Paired evaluations before public savings claims.

## Primary sources

- OpenAI, [Model guidance](https://developers.openai.com/api/docs/guides/latest-model), checked 2026-08-25. It recommends choosing model and reasoning effort for the workload, testing on representative tasks, and using higher effort only when measured quality justifies its cost.
- OpenAI, [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), checked 2026-08-25. It documents model and effort inheritance, per-agent overrides, orchestration by Codex, and the extra token use of subagent runs.
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), published 2024-12-19 and checked 2026-08-25. It recommends the simplest sufficient design, describes routing between cheaper and stronger models, and requires environmental evidence for agent progress.
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), published 2025-09-29 and checked 2026-08-25. It recommends small high-signal contexts and focused subagents when isolation pays for the extra work.
- Ong et al., [RouteLLM: Learning to Route LLMs with Preference Data](https://arxiv.org/abs/2406.18665), version 4, 2025-02-23.
- Chen, Zaharia, and Zou, [FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance](https://arxiv.org/abs/2305.05176), 2023-05-09.

External pages can change. The repository commit above anchors the code findings. The external claims need a fresh source check whenever a revalidation trigger fires.
