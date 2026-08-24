# Architecture

SkipHow exposes one conversational entrypoint. The router owns intent and mutation policy. It reads internal references only when a request needs them.

```text
user request
  -> intent and mutation authority
  -> project and repository instructions
  -> smallest sufficient internal path
  -> work or requested report
  -> result, evidence, limitations, follow-ups
```

## Policy ownership

| Concern | Canonical owner |
| --- | --- |
| Authority, scope, truthful completion | Repository or user instructions |
| Intent and mutation routing | `skills/skiphow/SKILL.md` |
| Product decision mechanics | `references/product/shape/` |
| Technical delivery | `references/engineering/cto/` |
| Durable campaign mechanics | `references/campaign/cto-run/` |
| Integration behavior | `references/trackers/` and `scripts/` |
| User experience | `README.md` |

Adapters point to canonical policy. They do not restate it.

## Product decisions

Ordinary work uses an ephemeral lightweight brief with outcome, required behavior, constraints, and acceptance evidence. An extended record is triggered by consequential, difficult-to-reverse, regulated, public-contract, migration, or multi-run decisions. Independent product review and durable acceptance evidence apply only when that extended decision or repository policy needs them.

The Owner controls vision, audience, portfolio priority, material scope, commercial constraints, cost and risk commitments, protected actions, and irreversible actions. The product controller resolves routine reversible behavior and recommends priority. The technical controller owns engineering decisions. Reviewers supply evidence.

## Technical delivery

Normal work uses `EXECUTE`. Unknown causes add a temporary `DIAGNOSE` branch. `CAMPAIGN` is selected only when coordination needs durable state for independent lanes, session recovery, dependency reconciliation, external waits, or useful parallel work.

Changed surfaces determine evidence and review. Authorization, data, billing, public contracts, infrastructure, and irreversible actions do not select orchestration by themselves.

Campaign state is sparse. It starts with `state.json`, `journal.jsonl`, and `briefing.md`. Decisions, evidence, receipts, and final output appear only when the run produces them. The final report is generated from reconciled state.

## Persistence

Core work has no tracker dependency. Persistence resolution is:

```text
configured canonical tracker
  or GitHub origin plus authenticated gh -> GitHub Issue
  or no tracker -> .skiphow/inbox.md
```

The local fallback is created only for an explicit capture request and never beside a different canonical tracker. Local IDs and provenance survive later migration.

GitHub Issues are canonical tracked units. The Project adapter accepts only an explicit `owner/number` configuration. A Project is an optional queue or status view, not a correctness dependency. Native issue types, parent and sub-issues, dependencies, and closing links are feature-detected.

The optional scripts have narrow contracts:

- `github_issues.py` checks availability, searches duplicates, persists an Issue, and links delivery.
- `github_project.py` updates an explicitly configured Project.
- `doctor.py` reports independent core, repository, Issues, Project, and host states without mutation.

## Host packaging

Codex packages the canonical skill at `plugins/skiphow/skills/skiphow/`. Claude Code exposes one adapter that loads the same policy. The default manifests contain no hooks, MCP server, remote service, credentials, telemetry, or bundled runtime.

## Verification

`scripts/check.py` owns deterministic local checks for tracked and new non-ignored files: structured files, links, portability scan, version consistency, metadata limits, eval corpus validation, tests, and whitespace. `scripts/check_hosts.py` owns official Codex validation and Claude package validation. Missing optional host proof is `UNVERIFIED` locally and blocking only where release policy explicitly requires it.

Behavioral verification has separate activation, routing, and repository outcome corpora. Outcome fixtures use real file and command tools, grade final repository state and forbidden side effects, and record efficiency metrics only as regression signals.
