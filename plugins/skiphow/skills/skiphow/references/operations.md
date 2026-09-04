# Operations

Open this when delivery health becomes part of the product result: slow or broken feedback, flaky CI, recurring manual work, dependency risk, an unclear release path, missing observability, a repeated incident, or a capability gap that the current team and tools cannot close safely.

## Keep the project releasable

Treat local setup, test data, CI, release paths, observability, documentation, dependency health, and recovery procedures as engineering assets. Repair a broken asset when it blocks or repeatedly taxes the requested result. Do not build process infrastructure for maturity's sake.

Prefer the shortest feedback loop that still represents the behavior. A slow comprehensive gate belongs near integration, while focused checks should answer local questions quickly. Classify a flaky check before trusting a pass. Repeated manual setup, copy steps, timeout increases, and one-off recovery commands are signals to remove the cause or record it as technical work.

Keep the integrated state releasable even when production deployment is outside authority. Know which checks protect the release, which action changes production, what rollback means for this product, and what evidence the destination returns. Never use a release rehearsal, package validator, or preview as proof that users received the change.

## Manage technical risk by product impact

Keep a technical roadmap only when sequencing must survive the current run. Tie each item to a product outcome, operational risk, or unblock value. Balance features, reliability, security, developer feedback, and debt by consequence rather than category quotas.

Estimate lifetime cost where it can change a decision: license and vendor spend, infrastructure, support, maintenance, migration, incident exposure, and the opportunity cost of complexity. Record a risk only when it is material and separable. Include the evidence, consequence, mitigation, owner decision if one exists, and the condition that should reopen it.

Bound work in progress by integration and review capacity. Starting more lanes than the lead can verify creates hidden inventory rather than speed. Prefer finishing and integrating a demonstrable slice before opening another that competes for the same boundary.

## Learn from failures

Classify a failure as product ambiguity, code, architecture, environment, host, missing capability, or process before choosing the remedy. Fix the systemic source when it will recur and the fix belongs in the authorized outcome. Otherwise preserve the evidence in the project's existing work system under [tracked work](tracked-work.md).

After an incident or repeated failure, keep the smallest durable fact that stops the next capable agent from repeating the investigation. Delete temporary diagnostics and stale recovery instructions. A transcript is not operational documentation.

Recommend specialist human review, procurement, or a capability investment only when the available agents, tools, and evidence cannot responsibly close a material gap. State the business consequence and the exact expertise or access needed. Do not transfer ordinary technical review back to the owner.
