# ADR 0010: One hook with two matcher groups; Codex evidence through project-level loading

## Status

Partially superseded by [ADR 0018](0018-autonomous-kernel-and-independent-task-skills.md). The read-only
startup/clear and compact/resume hook groups still load the owner kernel, and the receipt policy in
[ADR 0008](0008-receipts-over-a-live-harness.md) stands. The 1.x Codex project-loading workaround, fixed
queue fallback, and reviewer topology do not define 2.0.

## Date

2026-08-26

## Context

ADR 0007 shipped `hooks/hooks.json` with four `SessionStart` groups, one per source (`startup`, `clear`, `compact`, `resume`), two of which were byte-identical pairs. Both hosts' current hook documentation, read on 2026-08-26, says a `SessionStart` matcher may list several sources separated by `|` (Claude Code treats `startup|clear` as an exact list; Codex treats the matcher as a regex over the `source` field). Codex also documents that its `SessionStart` fires with source `compact` after automatic or manual compaction, which the 1.1 design assumed without a citation.

Every Codex behavior claim since 1.0 has been `UNVERIFIED` because this machine's managed Codex policy restricts marketplaces to allowed sources and rejects the local plain marketplace that `scripts/check_hosts.py` builds. The policy does allow the SkipHow Git source, so the installed plugin is whatever `main` held at the last upgrade, never the candidate. Codex loads skills from `$CWD/.agents/skills/` and hooks from `<repo>/.codex/hooks.json` without any marketplace, so a candidate can be exercised by symlinking `plugins/skiphow/skills/skiphow` into a fixture's `.agents/skills/skiphow` and copying `hooks/hooks.json` to `.codex/hooks.json`, with the installed plugin disabled for the run (`-c 'plugins."skiphow@skiphow".enabled=false'`). Those are the exact candidate bytes; only the packaging step is skipped.

`claude plugin eval` (with its no-plugin baseline arm) still answers "currently in early access" for this account on 2026-08-26, for both `init` and a run.

`scripts/check.py` still guarded against the return of runtime paths removed in 0.9 (`src/skiphow`, `schemas`, `pyproject.toml`, an adapters directory), four releases after their removal. The plugin top-level entry check already rejects anything unexpected inside the package.

## Decision

- `hooks/hooks.json` has two groups: `startup|clear` (invoke the skill; show unfinished work) and `compact|resume` (re-read the request and live state; show the checkpoint). The deterministic check requires each of the four sources to appear exactly once across the groups and keeps every other hook rule from ADR 0007.
- Codex receipts are produced by project-level loading of the exact candidate as described above and are recorded like any other receipt. This does not change the shipped package or the install instructions.
- Evaluation stays receipt-based (ADR 0008). `plugin eval` remains the intended path for comparative claims once it is available; until then the README labels the comparison a hypothesis.
- The queue for long work may come from `.skiphow/inbox.md` when the project has no tracker, so "save it" and "finish it" both work offline.
- The retired-runtime path guard leaves `scripts/check.py` and the tests.

## Consequences

The hook file halves with no behavior change on either host. Codex gains its first behavior receipts (see the [1.3 receipts](../research/2026-08-26/v1.3-receipts.md)). The Codex isolated install stays `UNVERIFIED` on this machine; CI still validates the package with the pinned Codex validator.

## Rejected alternatives

- One group with no matcher and a single combined message: works on both hosts, but the compaction message ("re-read the request and live state before acting") is the instruction that matters after compaction and would be diluted at every startup.
- Upgrading the installed Codex plugin from a release branch to test the candidate: the allowed Git source is the repository, not a ref, and it would leave the owner's install on a candidate.

## Evidence

- Claude Code hooks reference and Codex hooks documentation, read on 2026-08-26 (matcher lists, `SessionStart` sources, stdout as context).
- Codex skills documentation, read on 2026-08-26 (`$CWD/.agents/skills` precedence, symlinks followed).
- [1.3 receipts](../research/2026-08-26/v1.3-receipts.md).

## Revalidation triggers

Revisit when either host changes `SessionStart` matcher semantics or sources, when Codex allows a local marketplace under this policy, or when `plugin eval` becomes available to this project.
