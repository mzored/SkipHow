# ADR 0011: Tagged findings, shipped Codex role files, and neutral repository instructions

## Status

Accepted in 1.4.0. Amends [ADR 0007](0007-host-adapters-for-routing-and-continuity.md) (Codex routing path) and [ADR 0010](0010-two-matcher-hook-and-codex-project-loading.md) (evidence). [ADR 0008](0008-receipts-over-a-live-harness.md) and [ADR 0009](0009-reviewer-inherits-and-one-engineering-reference.md) stand.

## Date

2026-08-26

## Context

Findings outside the request were saved in 4 of 6 observed runs through 1.3. Transcripts from the [1.4 receipts](../research/2026-08-26/v1.4-receipts.md) show two causes: the authority rule made saving look ungranted, and "when material" invited dismissal for being unrelated. Prose fixes for each failed in a new way; a required tag per finding in the report held in the runs that followed.

Codex documentation read on 2026-08-26 still offers no tier aliases and no plugin-shipped agents; a project's `.codex/agents/<role>.toml` may set `model_reasoning_effort` and `sandbox_mode` and leave `model` unset. Since 1.1 the skill has described those files in prose and offered to write them.

`AGENTS.md` told any agent working on this repository that the package "carries exactly one hook and exactly three agent adapters" and must not add several named mechanisms. That is runtime architecture restated as a contributor rule, and it steers the agent that is supposed to challenge that architecture. The runtime skill likewise carried "never add a runner, daemon, task database, or model catalog", a rule about this repository, into every owner's project.

The paired evaluation showed the host baseline is strong on small tasks and that the skill costs two to three turns; the difference is where records go and how the report ends.

## Decision

- Every finding named in a report carries `TRACKED`, `SAVED`, or `DISMISSED` with its reason; saving a finding is always within authority; "outside the request" is not a dismissal reason; inbox entries use the intake block. The rule is in the root skill because it must apply on every route.
- The skill ships `codex-agents/scout.toml`, `builder.toml`, and `reviewer.toml` (sandbox and reasoning effort per role, no model), copied into a project's `.codex/agents/` when the owner asks. The check requires exactly those three files with `model` unset. This is role and effort routing on the session model, not capability-tier routing; Codex offers no stable capability name to route on. The 1.5 receipts observe all three roles with their effort levels on the session model.
- `AGENTS.md` holds only contributor rules: evidence standards, checks, portability and safety. The accepted package shape lives in the ADRs and is enforced by `scripts/check.py`, which changes together with a new ADR. The runtime skill no longer carries repository guardrails.
- Paired with-and-without runs are recorded once per release in `docs/research/<date>/paired-eval.md` with `scripts/run_summary.py`; three tasks, one run per arm, judged by reading the result. This is a regression check, not a benchmark.

## Consequences

Findings behave as an invariant rather than a judgment (4 of 4 after the tag, on a small sample). Codex owners get routing with one sentence. A future developer reads a neutral `AGENTS.md` and the ADRs as dated evidence. The README states the measured overhead and where the difference was.

## Rejected alternatives

- A hook or check that scans the report for untagged findings: the host has no report event, and the tag held without it.
- Auto-writing `.codex/agents/` on first use: writes into the owner's project without a request.
- Keeping the package-shape sentence in `AGENTS.md` "for safety": the check enforces it; the sentence only biased the reader.

## Evidence

- [1.4 receipts](../research/2026-08-26/v1.4-receipts.md), [paired evaluation](../research/2026-08-26/paired-eval.md)
- Codex custom agents and skills documentation, read on 2026-08-26

## Revalidation triggers

Revisit when a finding is again named without a tag in a receipt, when Codex ships tier aliases or plugin agents, or when a paired run shows the skill losing correctness against the baseline.
