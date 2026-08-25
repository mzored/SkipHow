# Release-readiness audit after the host-native rewrite

## Scope

- Audited baseline: `5b189278a8840553ce014f3bed9459ff292b1ef1` on `main`.
- Local hosts inspected: Codex CLI 0.149.1 and Claude Code 2.1.240.
- Surfaces: owner UX, installed skill policy, GitHub lifecycle, recovery, semantic model routing, package contents, deterministic checks, and opt-in live evaluation.
- Paid model trials and mutable GitHub delivery were not run.

This audit checked the previous release summary against the repository and current host behavior. Six independent read-only reviews covered architecture, GitHub lifecycle, packaging, routing, tests and security, and README UX.

## Findings that changed the release candidate

### Authority and recovery

The installed skill did not preserve enough trusted state to resume protected actions after compaction. The checkpoint now includes selected scope, current authority and later restrictions, accepted decisions, queue and dependencies, Issue, branch, worktree, pull request, exact head, owned resources, last external action and result, evidence, blockers, and next safe action. Missing or conflicting authority, ownership, or exact state blocks merge and cleanup.

Pause, cancellation, and narrower authority now revoke merge authority, disable owned auto-merge, leave an owned merge-queue entry when possible, and confirm the result. GitHub documents auto-merge and merge queues as separate pending actions that need explicit control: [auto-merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request) and [merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue).

Delivery authority now explicitly permits one deduplicated record for each material independent finding. It does not permit implementation or reprioritization of that finding. Intake applies the same privacy, provenance, duplicate, and append-only rules to requested records and delivery findings.

Cross-run GitHub safety no longer relies on one root agent serializing only its own session. Before claiming work or taking a protected action, the agent checks Issues, linked pull requests, branches, and stable markers for a competing operation.

### Model routing

Neither host accepts `FAST`, `STANDARD`, or `DEEP` as a portable capability request. Codex and Claude accept concrete model choices or inheritance for subagents, subject to current host configuration and substitution. See [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).

The root now maps a semantic tier only from current capability, cost, or latency metadata exposed by the host. It selects the concrete route at subagent spawn and does not infer capability or price from a name. Without trustworthy mapping data, per-agent choice, or effective-route telemetry, inheritance is the safe fallback and model selection remains `UNVERIFIED`.

The routing evaluator supplies an operator-owned map. It can measure cost ablation for those controlled routes, not autonomous selection by SkipHow. Those claims are now separate.

### Package and evaluation security

The distributed plugin declared MIT but omitted the license text. `plugins/skiphow/LICENSE` now matches the repository license, and deterministic checks enforce that copy.

Remote Codex marketplace installation may clone the source into host cache state. An exact remote ref therefore still violates the rule that release checks do not create or delete a repository. Version and enabled state also do not prove installed bytes. Package checks now create a plain local marketplace snapshot and compare the installed payload with the candidate. Codex issue [#34321](https://github.com/openai/codex/issues/34321) is a direct upstream example of inventory state not proving usable payload, and [#32829](https://github.com/openai/codex/issues/32829) records Git-backed marketplace materialization.

Receipt redaction previously covered command output but not nested structured collector evidence. Structured collectors no longer return raw JSON, inbox records, workspace roots, or GitHub snapshots. Every receipt write applies recursive redaction.

Claude's current `--bare` mode skips project customizations while preserving explicitly supplied plugins. The evaluator also requires sandbox startup and disables unsandboxed command fallback. Those controls protect synthetic plain-workspace trials. They do not solve mutable GitHub evaluation because commits require Git metadata writes. The harness therefore blocks that scenario before credentials or host execution. See the official [Claude CLI](https://code.claude.com/docs/en/cli-reference), [settings](https://code.claude.com/docs/en/settings#sandbox-settings), and [sandbox](https://code.claude.com/docs/en/sandboxing) documentation.

## Release interpretation

The architecture is suitable for a 0.9 preview after deterministic and host package checks pass on the final tree. It is not evidence for a stable 1.0 claim of unattended multi-Issue delivery, restart continuity, autonomous model selection, or routing savings. Those outcomes remain `UNVERIFIED`.

README copy now describes policy rather than claiming technical enforcement. It also makes host-specific invocation and the difference between `save` and `implement` explicit.

## Final local evidence

The final audited worktree passed:

- `python scripts/check.py`;
- 55 repository-managed pytest tests;
- `python evals/live/run.py validate` for all ten versioned scenario contracts;
- Codex and Claude package validation;
- Claude isolated installation with exact installed-payload comparison;
- `git diff --check`.

Codex isolated installation is `UNVERIFIED` in this environment because managed policy rejects a filesystem marketplace. The audit did not use the permitted Git-source alternative because that path can create and later delete a repository in host cache state. No paid model or mutable GitHub trial ran.

## Revalidation triggers

Repeat this audit when host plugin formats, sandbox behavior, subagent model selection, GitHub merge semantics, or receipt telemetry change. A future GitHub live gate needs an enforced repository-preservation boundary, not another confirmation flag.
