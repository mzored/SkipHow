# Architecture

SkipHow ships portable workflows and thin host adapters. Each workflow under `plugins/skiphow/skills/` is canonical. Host adapters only tell each host how to reach it.

## Canonical skills

The plugin separates owner intent, product direction, technical control, focused engineering capabilities, and durable execution:

- `skiphow` routes the request and enforces the Owner, Product Director, and CTO authority boundary.
- `idea` captures without shaping.
- `shape` produces a reviewed Product Contract without prescribing implementation.
- `develop` freezes approved work and hands it to the CTO for proportionate delivery.
- `fix` routes defects through normal execution, internal diagnosis when the cause is unknown, or a product decision when expected behavior is ambiguous.
- `cto` is the internal technical controller. It chooses `EXECUTE`, `DIAGNOSE` then `EXECUTE`, or a durable `CAMPAIGN`, and owns architecture, reuse, testing, review, sequencing, and integration.
- `diagnose` is the focused diagnostic loop for explicit analysis requests and for causes that remain unclear during repair.
- `testing`, `codebase-design`, `technical-review`, `prototype`, and `resolving-merge-conflicts` are internal engineering capabilities selected by the CTO.
- `setup` reuses or bootstraps the standard minimal GitHub Project for an explicit setup request.
- `preflight` checks local and GitHub lifecycle prerequisites without changing them and reports `READY`, `SETUP_NEEDED`, or `DEGRADED`.
- `cto-run` supplies durable state, recovery, lane coordination, and final reconciliation for campaigns that need it.
- `github-task` performs native GitHub Issue and standard Project lifecycle operations only after the owning workflow classifies work as tracked.

Shared technical policy lives under `plugins/skiphow/skills/cto/`. The `cto-run` skill reads that policy, then adds only durable mechanics. It requires explicit invocation by the user or selection by the CTO after inspection. It is not a stricter development mode or a general workflow engine. Multiple independent workstreams, session boundaries, dependency graphs, external waits, materially useful parallelism, and recovery needs determine whether work becomes a campaign.

The controller answers six questions in sequence: requested outcome, smallest coherent scope, unresolved desired interaction or state model, unresolved causal uncertainty, durable orchestration need, and evidence required by the changed surfaces. Authority applies in parallel. It does not materialize these concerns as a Cartesian state matrix. A design question may use one disposable prototype before normal execution. Unknown causes enter diagnosis and return to normal execution after the root cause is known. Authentication, persisted data, billing, public contracts, production infrastructure, shared primitives, and irreversible actions strengthen evidence without selecting orchestration.

Owner-facing entrypoints share that controller instead of embedding separate engineering methods: `fix` uses `EXECUTE` when the cause is known and `DIAGNOSE` then `EXECUTE` when it is not; `develop` uses `EXECUTE` unless a campaign is genuinely needed; `diagnose` reports after root-cause proof when analysis alone was requested; and explicit `cto-run` is the advanced campaign entrypoint.

The scope firewall and finding lifecycle are one rule. Every material finding reaches `RESOLVED`, `PERSISTED`, `DUPLICATE`, or `DISMISSED`, preventing both silent loss and accidental scope expansion. A tracker is loaded only after work is already known to be tracked or a finding has been classified `PERSISTED`; the adapter cannot decide scope, methods, review, or orchestration.

Review and validation converge by delta. The first required review covers the relevant integration diff; fixes receive scoped re-review unless they materially change architecture, accepted scope, product behavior, a protected surface, or the effective diff. New state invalidates evidence semantically and proportionally, not globally because an identity changed. Product acceptance is repeated only for contract-visible semantic changes. Unavailable optional proof is recorded as `UNVERIFIED`; unavailable release-required proof remains an external prerequisite instead of authorizing new validation infrastructure.

Product acceptance is SkipHow's project-specific implementation of an intent check, not a universal engineering phase. When user-facing semantics change under a Product Contract, the Product Director checks runtime, rendered, API, or other product evidence against the contract. Behavior-preserving later deltas carry that evidence forward. A mismatch returns to the CTO. A requested behavior change returns to `shape`.

## Instruction ownership

Each rule has one owner. Other layers reference it instead of restating it:

| Layer | Owns |
| --- | --- |
| Global user instructions | Authority, universal working principles, and truthful completion |
| Engineering controller | Routing, scope firewall, evidence semantics, and finding lifecycle |
| Repository policy | Architecture, product sources of truth, protected surfaces, and required gates |
| On-demand skills | The mechanics of diagnosis, review, research, testing, and other techniques |
| Adapters and host configuration | Tracker, CI, deployment, models, concurrency, credentials, and machine-specific commands |

Stable cross-project rules belong in global instructions or the controller. Repository-specific rules belong in repository policy. Technique-specific rules belong in the relevant skill. Provider, account, or machine details belong in adapters or host configuration.

Existing domain glossaries and ADRs are consumed as source material. A glossary changes only when a durable domain concept changes. An ADR is created only for a consequential, hard-to-reverse, non-obvious trade-off. Human-only credentials, dashboards, migrations, or protected actions use a precise handoff and post-action verification instead of a mandatory wizard format.

The plugin has no MCP server, telemetry, remote service, credential flow, or bundled runtime. Hosts supply filesystem access, command execution, task controls, and connected services. GitHub lifecycle support adds local plugin hooks and a bundled Python helper. It requires Python 3.10 or newer, `git`, and authenticated `gh` 2.93.0 or newer. Claude Code on native Windows additionally uses the Git Bash shipped by Git for Windows so one shell-form hook can select `python3`, `python`, or `py -3` without duplicating lifecycle policy.

## GitHub lifecycle integration

Verdict: `INTEGRATE`.

SkipHow uses the official GitHub CLI for authentication, Issues, Project v2 mutations, and narrow GraphQL queries. GitHub Issues are the durable work identity; a linked Project is the default human-facing queue and status control panel; pull requests are implementation artifacts. Native issue types, sub-issues, dependencies, and closing links carry semantics that previously required labels or Markdown conventions. One bundled standard-library Python helper filters Project v2 responses down to the board, queue, item, or verification line the workflow needs. Codex discovers `plugins/skiphow/hooks/hooks.json` at its default plugin path. The Claude manifest points to the same canonical file, and its root script is a small adapter to the canonical helper inside the Codex package.

The alternative was a second GitHub client library such as PyGithub. It would add dependency installation, version management, and another authentication path, but it would not replace host hook handling or the Project v2 GraphQL queries. A remote service was rejected because lifecycle state already lives in GitHub and the plugin does not need another credential or availability boundary. A personal helper path was rejected because installed plugins must be portable.

Dependency check recorded on 2026-08-24: the [GitHub CLI repository](https://github.com/cli/cli) declares the MIT license, [v2.98.0](https://github.com/cli/cli/releases/tag/v2.98.0) was released on 2026-08-20, and the project is past pre-1.0. The public contributor history has several active contributors, but the number of maintainers is unverified because the repository does not publish that role. GitHub's high-severity advisories [GHSA-8xvp-7hj6-mcj9](https://github.com/cli/cli/security/advisories/GHSA-8xvp-7hj6-mcj9) and [GHSA-p2h2-3vg9-4p87](https://github.com/cli/cli/security/advisories/GHSA-p2h2-3vg9-4p87) affect ranges through v2.92.0 and v2.61.0, so SkipHow requires v2.93.0 or newer. The exact validation host used v2.97.0.

The standard Project stays deliberately small: `Status` has `Backlog`, `Ready`, `In progress`, `Waiting`, and `Done`; saved views expose the board, active work, and items needing attention. Setup prefers built-in auto-add and completion workflows. It does not require `Human Gate`, risk, execution, review, validation, or agent fields, and it does not create a label taxonomy. Project absence is `SETUP_NEEDED` when setup can repair it and `DEGRADED` when permissions or platform support prevent it. Issue-only engineering remains valid in degraded mode.

The hooks guard configured lifecycle state only. `PreToolUse` respects an existing non-empty legacy `Human Gate` when a repository still has one, but the field is never required. `Stop` catches a linked task branch whose configured Status is still unstarted. The skill sets `In progress` only after branch creation and linkage are confirmed, avoiding remote mutation from host PostToolUse events that do not expose shell success consistently. The owning workflow remains responsible for deciding whether tracking exists and for all engineering work.

Hosts may disable or refuse plugin hooks through their own policy. In that case the `github-task` skill still exposes explicit lifecycle commands, but automatic claim and stop checks are unavailable.

## Claude Code adapter

Claude Code loads the adapters under `adapters/claude/skills/`. Each adapter directs Claude Code to its canonical skill instead of copying policy. The `cto-run` adapter disables model invocation; the owner-facing routing skills may activate when their descriptions match. Codex installs the nested `plugins/skiphow/` package and loads its `skills/` directory directly. Keeping that package below the repository root prevents Claude Code from discovering both copies.

This keeps behavior in one place. A workflow change belongs in its canonical skill, not in an adapter.

## Capability roles

The operating policy uses capability roles instead of provider-specific model names:

- `MECHANICAL` workers handle bounded extraction and deterministic commands.
- `IMPLEMENTATION` workers own scoped changes, ordinary debugging, and synthesis.
- `CTO_REVIEW` workers make architecture decisions, investigate repeated anomalies, and perform the final independent integration review.

The active host maps available agents to those roles and records any limitation in a receipt.

## Engineering references

The testing, technical-review, codebase-design, prototype, and resolving-merge-conflicts skills wrap or adapt selected MIT-licensed material from `mattpocock/skills`. The project released v1.2.3 on 2026-08-06. SkipHow pins later source commit `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`. Maintainer count and high-severity advisory status are unverified. The imported files are Markdown and YAML, not runtime dependencies.

SkipHow's wrappers take priority over upstream process. The CTO chooses test seams and whether TDD adds value. One fresh reviewer can cover separate Spec and Standards axes when independent review is required. A security, privacy, data, authorization, compatibility, operations, or other specialist lens is added only when the changed surface needs it. Subagents isolate large exploration, supply fresh review context, or own genuinely independent write tracks; they are not a ritual triggered by a label or file count.

## Behavioral evaluations

The shared JSON corpus under `plugins/skiphow/evals/` covers request routing, execution shape, Owner questions, tracker touches, campaign creation, testing selection, review convergence, and product acceptance. It includes positive and negative cases from real failure modes and judges outcomes rather than a fixed tool-call sequence. Offline verification validates its schema and representative coverage. Codex and Claude Code adapters can run every case as an opt-in structured model evaluation and record available token, turn, tool-call, campaign, and tracker signals as secondary metrics. Live runs are separate from CI because they consume host resources and can vary across models.

## Durable state

A run directory must contain these root files:

```text
state.json
journal.jsonl
briefing.md
FINAL.md
```

It also contains `decisions/`, `evidence/`, and `receipts/`. After recovery, the root agent rebuilds the current picture from these files and primary systems. Prior summaries and worker reports are claims until checked.

## Release gates

`python scripts/verify_release.py --base <base-sha>` is the deterministic release entrypoint. It parses JSON and YAML, runs the official Codex plugin validator, validates the behavioral corpus, scans distributable source and manifests for personal paths, checks local Markdown links, runs the repository suite, and checks whitespace in both the working tree and full candidate diff. Local runs resolve the validator from the active `CODEX_HOME`. CI checks out the official OpenAI validator at pinned commit `333beecd41281b1350688b417a2f20c66e2a743e` and supplies its path through `CODEX_PLUGIN_VALIDATOR`.

The release gate enumerates candidate-owned files through Git so ignored and untracked workspace state cannot change the result. Markdown links are parsed with `markdown-it-py` 4.2.0 rather than a repository-specific parser. This is an `INTEGRATE` decision: extending the existing regular expression was rejected because CommonMark destinations and references need a real parser, while a separate link-checking CLI would add another runtime and CI integration. The library fits the existing Python gate, is MIT licensed, stable, supports Python 3.10+, and released in May 2026. PyPI lists one maintainer, so the more-than-one-maintainer check is unverified; the repository has multiple recent contributors but that is not treated as maintainer evidence. The project is post-1.0 and lists no published advisories for the current line; a historical pre-2.2.0 denial-of-service advisory is fixed. No comprehensive third-party CVE audit was available, so absence of other high-severity issues remains unverified.

`python scripts/verify_release.py --host` is the exact-candidate host gate. It requires a clean commit, records the commit and host versions, validates the Claude plugin strictly, and installs the local marketplace candidate into isolated Codex and Claude homes. It fails when an installed host cannot validate or install the candidate. It does not publish, deploy, or mutate the user's normal host configuration.
