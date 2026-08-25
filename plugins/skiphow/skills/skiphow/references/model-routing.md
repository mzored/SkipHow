# Model routing

Choose models by the work they must do. Keep model names out of shared policy because hosts and catalogs change.

## Separate the decisions

Decide task type, execution shape, capability tier, and reasoning effort separately. Do not call another model merely to route the task.

Use these semantic tiers:

- `FAST` handles bounded read-only search, inventory, extraction, log scanning, and fact checks with clear outputs.
- `STANDARD` handles normal implementation, debugging, tests, and documentation.
- `DEEP` handles product shaping, architecture, security, an unknown cause, build-versus-reuse research, integration across contracts or systems, and independent high-risk review. Treat authentication, data boundaries, and public-contract changes as material.

The root agent and final integrator inherit the model selected by the user or host. For an independent subagent, the root agent maps a tier only from current capability, cost, or latency metadata exposed by the host. It then selects the concrete route when spawning the subagent. Do not infer capability or price from a model name. If the host exposes no trustworthy mapping data or no per-agent choice, inherit the current model and treat model selection and claimed savings as `UNVERIFIED`.

Use `FAST` only for work that is narrow, independent, and easy to check. Do not assign ordinary code changes to a cheap model by default. Keep a mutable task on one tier until a checkpoint.

Reasoning effort is not a model tier. Start with the host's normal effort. Record the effective model and effort when the host reports them; a substituted or inherited route is not proof of the requested tier. Retry a transient tool or service failure on the same route. After one substantive verification failure, allow one corrective attempt at the same tier. Promote only after a repeated reasoning failure or direct evidence that the current model lacks the required capability. A promotion counts only when the effective model or effort changes. Reclassify the task at a checkpoint if new security or architecture risk changes the work itself. Do not lower the tier midway through mutable work.

Use independent `DEEP` review for security changes, public contracts, large integrations, weak verification, or repeated failure. Ordinary changes need self-review and relevant tests, not a mandatory panel.

After one correction and one effective promoted or independent review attempt fail on the same premise, record `BLOCKED`. Do not loop at `DEEP` or repeat a promotion that resolves to the same effective route.

Measure the full cost of a verified result. Include root context, delegated work, handoffs, retries, and review. Do not claim lower cost or faster delivery until paired evaluations preserve outcome quality.
