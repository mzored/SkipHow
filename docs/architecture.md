# Architecture

SkipHow exposes one conversational entrypoint. Its kernel preserves the original request, resolves intent and mutation authority, inspects repository instructions, and selects the smallest sufficient internal path.

```text
request -> authority and project context -> surface dispatch -> work -> evidence
```

## Kernel

The kernel owns routing, scope, mutation boundaries, final intent alignment, and truthful completion. It does not require a tracker, campaign, review, TDD, product acceptance, hooks, subagents, or an external service.

`CHANGE` keeps one public meaning but has an internal surface dispatch. Software behavior and repository mechanics use technical delivery policy. Documents, research reports, interface copy, and other non-software project artifacts execute directly under repository instructions with evidence suited to the artifact. Factual work uses current authoritative sources; visual work uses an available render or preview.

Normal technical work executes directly. An unknown cause adds temporary diagnosis. Durable campaign state appears only when independent lanes, external waits, session recovery, or reconciliation need it. Risk changes the required evidence, not the orchestration shape.

## Policy ownership

| Concern | Canonical owner |
| --- | --- |
| Intent, authority, and surface dispatch | `skills/skiphow/SKILL.md` |
| Technical delivery and evidence | `references/engineering/cto/` |
| Product decision mechanics | `references/product/shape/` |
| Durable campaign mechanics | `references/campaign/cto-run/` |
| Tracker behavior | `references/trackers/` and `scripts/` |
| Host capability vocabulary | `references/host-capabilities.md` |

Adapters point to these owners. They do not copy policy.

## Host capability contract

The controller selects mechanisms by capability, not by product name. The vocabulary is:

- `inspect_project`
- `mutate_project`
- `run_local_commands`
- `optional_external_verifier`
- `research_external_sources`
- `delegate_read_only`
- `delegate_mutable_lane`
- `fresh_independent_review`
- `persist_external_work`
- `perform_protected_action`

Missing delegation does not block bounded work; one agent can execute it sequentially. A required independent review without a fresh-review capability remains `UNVERIFIED` or follows a repository-defined blocker. Protected actions still need the authority the host and user require.

Product support is not architecture truth. The README reports package validation separately from runtime behavior. Package checks do not prove how a model will interpret the installed instructions.

## Campaign state

A campaign records the immutable requested outcome, lane ancestry, budget envelope, stop state, progress policy, claims, checkpoints, and monotonic transitions. The minimal durable files are `state.json`, `journal.jsonl`, and `briefing.md`; other records appear only when produced.

The campaign controller can recover an orphaned lane and reconcile final state. It does not add a server, scheduler, database, dashboard, default heartbeat, or unattended control plane.

## Persistence and configuration

Core work has no persistence dependency. Explicit capture resolves the configured tracker, then the available GitHub Issue adapter, then the local `.skiphow/inbox.md` fallback. A GitHub Project is an optional projection and never lifecycle authority.

Optional helpers share `.skiphow/config.json`. Its schema has only `tracker`, `project`, and `campaign_root`. Missing configuration is the zero-config state. The parser rejects unknown keys, invalid tracker values, absolute campaign roots, and traversal outside the project.

## Extension contract

Future domain or integration extensions stay internal and lazy. Each extension declares:

- trigger and negative trigger;
- owning authority and required inputs;
- allowed local and remote mutations;
- protected actions;
- output and evidence contract;
- fallback when unavailable;
- context budget and deterministic regression coverage;
- source and license when adapted.

An extension belongs outside the kernel unless an observed failure and a deterministic regression test show that every request needs it.

## Verification

Deterministic checks cover structured files, links, portability, version consistency, instruction budgets, runtime policy contracts, tests, and whitespace. Direct contract tests protect the mutation boundary, campaign threshold, scoped re-review, verification limits, and verbatim user intent.

Host availability and package proof are separate. Finding a CLI does not prove that the package installs. Package validation and isolated installation do not prove skill activation or model behavior. This repository does not launch models as part of tests or release checks.
