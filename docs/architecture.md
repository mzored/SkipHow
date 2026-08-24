# Architecture

SkipHow ships portable workflows and thin host adapters. Each workflow under `plugins/skiphow/skills/` is canonical. Host adapters only tell each host how to reach it.

## Canonical skills

The plugin separates owner intent, product direction, technical control, focused engineering capabilities, and durable execution:

- `skiphow` routes the request and enforces the Owner, Product Director, and CTO authority boundary.
- `idea` captures without shaping.
- `shape` produces a reviewed Product Contract without prescribing implementation.
- `develop` freezes approved work and hands it to the CTO for proportionate delivery.
- `fix` routes defects through a direct repair, internal diagnosis, product decision, or CTO control according to evidence.
- `cto` is the internal technical controller. It chooses direct, tracked-direct, or durable execution and owns architecture, reuse, testing, review, sequencing, and integration.
- `diagnose` is the internal diagnostic loop for causes that remain unclear after initial inspection.
- `testing`, `codebase-design`, and `technical-review` are internal engineering capabilities selected by the CTO.
- `preflight` checks local and GitHub lifecycle prerequisites without changing them.
- `cto-run` supplies durable state, recovery, lane coordination, and final reconciliation for campaigns that need it.
- `github-task` performs GitHub issue and Project v2 lifecycle operations only after the owning workflow classifies work as tracked.

Shared technical policy lives under `plugins/skiphow/skills/cto/`. The `cto-run` skill reads that policy, then adds only durable mechanics. It requires explicit invocation by the user or selection by the CTO after inspection. Risk controls review and validation depth. Multi-task work, external waits, session boundaries, coordinated lanes, and recovery needs control whether work becomes a durable campaign.

The controller classifies scope, execution shape, risk, lifecycle durability, and authority independently. Unknown causes enter diagnosis and are classified again after the root cause is known. Every material finding reaches `RESOLVED`, `PERSISTED`, `DUPLICATE`, or `DISMISSED`, which prevents both silent loss and accidental scope expansion.

Review and validation converge by delta. The first required review covers the relevant integration diff; fixes receive scoped re-review unless they materially change architecture, accepted scope, product behavior, a protected surface, or the effective diff. Changed commits invalidate only affected engineering evidence. Product acceptance is repeated only for contract-visible semantic changes. Unavailable optional proof is recorded as `UNVERIFIED`; unavailable release-required proof remains an external prerequisite instead of authorizing new validation infrastructure.

User-visible work governed by a Product Contract gets Product Director acceptance at the exact implementation candidate. The Product Director checks runtime, rendered, API, or other product evidence against the contract. A mismatch returns to the CTO. A requested behavior change returns to `shape`.

The plugin has no MCP server, telemetry, remote service, credential flow, or bundled runtime. Hosts supply filesystem access, command execution, task controls, and connected services. GitHub lifecycle support adds local plugin hooks and a bundled Python helper. It requires Python 3.10 or newer, `git`, and authenticated `gh` 2.93.0 or newer. Claude Code on native Windows additionally uses the Git Bash shipped by Git for Windows so one shell-form hook can select `python3`, `python`, or `py -3` without duplicating lifecycle policy.

## GitHub lifecycle integration

Verdict: `INTEGRATE`.

SkipHow uses the official GitHub CLI for authentication, Issues, Project v2 mutations, and narrow GraphQL queries. One bundled standard-library Python helper filters Project v2 responses down to the board, queue, item, or verification line the workflow needs. Codex discovers `plugins/skiphow/hooks/hooks.json` at its default plugin path. The Claude manifest points to the same canonical file, and its root script is a small adapter to the canonical helper inside the Codex package.

The alternative was a second GitHub client library such as PyGithub. It would add dependency installation, version management, and another authentication path, but it would not replace host hook handling or the Project v2 GraphQL queries. A remote service was rejected because lifecycle state already lives in GitHub and the plugin does not need another credential or availability boundary. A personal helper path was rejected because installed plugins must be portable.

Dependency check recorded on 2026-08-24: the [GitHub CLI repository](https://github.com/cli/cli) declares the MIT license, [v2.98.0](https://github.com/cli/cli/releases/tag/v2.98.0) was released on 2026-08-20, and the project is past pre-1.0. The public contributor history has several active contributors, but the number of maintainers is unverified because the repository does not publish that role. GitHub's high-severity advisories [GHSA-8xvp-7hj6-mcj9](https://github.com/cli/cli/security/advisories/GHSA-8xvp-7hj6-mcj9) and [GHSA-p2h2-3vg9-4p87](https://github.com/cli/cli/security/advisories/GHSA-p2h2-3vg9-4p87) affect ranges through v2.92.0 and v2.61.0, so SkipHow requires v2.93.0 or newer. The exact validation host used v2.97.0.

The hooks guard adopted lifecycle state only. `PreToolUse` prevents branch creation when a tracked item's Human Gate is not `No`; it fails open when the repository or issue is not on an adopted board. `Stop` catches a linked task branch whose board item is still unstarted. The skill sets `In Progress` only after branch creation and linkage are confirmed, avoiding remote mutation from host PostToolUse events that do not expose shell success consistently. The owning workflow remains responsible for deciding whether tracking exists and for all engineering work.

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

The testing, technical-review, and codebase-design skills wrap selected MIT-licensed material from `mattpocock/skills`. The project released v1.2.3 on 2026-08-06. SkipHow pins later source commit `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`. Maintainer count and high-severity advisory status are unverified. The imported files are Markdown and YAML, not runtime dependencies.

SkipHow's wrappers take priority over upstream process. The CTO chooses test seams and whether TDD adds value. One fresh reviewer can cover separate Spec and Standards axes for R2. A security, privacy, data, or authentication lens is added only when the changed R3 area needs it. Codebase design does not force an Owner checkpoint or a fixed number of agents.

## Behavioral evaluations

The shared JSON corpus under `plugins/skiphow/evals/` covers request routing, Owner questions, lifecycle ceremony, durability, testing selection, review depth, and product acceptance. Offline verification validates its schema and representative coverage. Codex and Claude Code adapters can run every case as an opt-in structured model evaluation. Live runs are separate from CI because they consume host resources and can vary across models.

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
