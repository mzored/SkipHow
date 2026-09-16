# Operations

Open this when delivery health becomes part of the product result: slow or broken feedback, flaky CI, recurring manual work, dependency risk, an unclear release path, missing observability, a repeated incident, or a capability gap that the current team and tools cannot close safely.

## Keep the project releasable

Treat local setup, test data, CI, release paths, observability, documentation, dependency health, and recovery procedures as engineering assets. Repair a broken asset when it blocks or repeatedly taxes the requested result. Do not build process infrastructure for maturity's sake.

Prefer the shortest feedback loop that still represents the behavior. A slow comprehensive gate belongs near integration, while focused checks should answer local questions quickly. Classify a flaky check before trusting a pass. Repeated manual setup, copy steps, timeout increases, and one-off recovery commands are signals to remove the cause or record it as technical work.

Promote one immutable candidate through later release stages. Reuse checks attached to its revision or artifact while their inputs remain equivalent; do not recertify the same state merely because its stage name changed. Add an environment-specific check only for a property earlier evidence could not establish.

Keep the integrated state releasable even when production deployment is outside authority. Know which checks protect the release, which action changes production, what rollback means for this product, and what evidence the destination returns. Never use a release rehearsal, package validator, or preview as proof that users received the change.

## Diagnose verification friction

When verification friction recurs or becomes materially expensive, measure the actual cost before choosing a remedy. Inspect execution and setup timing, retries and flakes, service startup, dependency installation, test-data preparation, serialization, duplicated coverage, and CI topology where relevant. Fix the layer responsible for the cost. A slow suite does not prove tests should be deleted, substantial browser coverage does not prove the browser tests are the bottleneck, and a fast suite does not prove important integrated behavior is covered.

Preserve useful evidence while repairing the system. Do not hide degradation by weakening assertions, skipping useful coverage, increasing timeouts, adding retries, or moving important evidence outside the delivery path without an equivalent reliable signal. Repair a small verification-system defect when it naturally belongs to the authorized outcome. When the remedy is material and separable, preserve the finding with evidence through [tracked work](tracked-work.md) instead of silently widening the request.

## Manage technical risk by product impact

Keep a technical roadmap only when sequencing must survive the current run. Tie each item to a product outcome, operational risk, or unblock value. Balance features, reliability, security, developer feedback, and debt by consequence rather than category quotas.

Estimate lifetime cost where it can change a decision: license and vendor spend, infrastructure, support, maintenance, migration, incident exposure, and the opportunity cost of complexity. Record a risk only when it is material and separable. Include the evidence, consequence, mitigation, owner decision if one exists, and the condition that should reopen it.

Bound work in progress by integration and review capacity. Starting more lanes than the lead can verify creates hidden inventory rather than speed. Prefer finishing and integrating a demonstrable slice before opening another that competes for the same boundary.

## Learn from failures

Classify a failure as product ambiguity, code, architecture, environment, host, missing capability, or process before choosing the remedy. Fix the systemic source when it will recur and the fix belongs in the authorized outcome. Otherwise preserve the evidence in the project's existing work system under [tracked work](tracked-work.md).

After an incident or repeated failure, keep the smallest durable fact that stops the next capable agent from repeating the investigation. Delete temporary diagnostics and stale recovery instructions. A transcript is not operational documentation.

Recommend specialist human review, procurement, or a capability investment only when the available agents, tools, and evidence cannot responsibly close a material gap. State the business consequence and the exact expertise or access needed. Do not transfer ordinary technical review back to the owner.
