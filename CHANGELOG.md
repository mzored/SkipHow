# Changelog

All notable changes to this project appear in this file.

## 1.10.0 (2026-08-27)

SkipHow 1.10 moves the two delegation rules that bind unconditionally out of the reference no run opens.

### Changed

- A session decomposed an owner request into eight delegates across isolated worktrees and never loaded `model-routing.md`. That is 5 of 5 delegating sessions, and the governing sentence is identical in every version audited ([field audit](docs/research/2026-08-27/field-audit-2026-08-27.md)).
- Its routing was correct anyway. The shipped agent definitions carry the tier in their own descriptions, so a run picks `builder` or `reviewer` from the host's agent listing without reading anything. The observed models were `claude-sonnet-5` for all five builders and the session model for all three reviewers — the first field evidence that [ADR 0007](docs/decisions/0007-host-adapters-for-routing-and-continuity.md) and [ADR 0009](docs/decisions/0009-reviewer-inherits-and-one-engineering-reference.md) resolve at runtime. Earlier research recorded that "the tiers are documentation"; they are not, and that line is no longer `UNVERIFIED`.
- What the reference held alone was the brief contract and the failure-escalation ladder, and those reached nobody. [ADR 0016](docs/decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) had named measuring exactly this as the next receipt's job. Both rules move into the root beside the delegation sentences, `model-routing.md` stops repeating them per [ADR 0015](docs/decisions/0015-unconditional-invariants-live-in-the-root.md), and the reference keeps only what is genuinely conditional: which tier a job needs, the Codex spawn mechanics, and the effective-model rule.
- The same session carried a five-item queue, parallel worktrees, external waits, and an owner turn calling the change systemic, and wrote no handoff at any point. 1.9.0's rewritten trigger would have fired on it, so this is a receipt request against 1.9.0 rather than a change: the decomposition fix is still unseen in the field.
- The root's escalation ladder is scoped to the unit that failed. `long-work.md` already told a queue run to mark the item `BLOCKED` and move on, so a ladder in the root ending "stop and report" would have contradicted it on every queue — the two sentences had never been in context together before, because neither reference reliably loads.
- The root budget rises from 850 words to 1,000, and 6,000 bytes to 7,000. The move left the root at 847 of 850, and three words of slack is the condition [ADR 0015](docs/decisions/0015-unconditional-invariants-live-in-the-root.md) exists to prevent: it is a drift guard, never a target to compress toward. That ADR's own third revalidation trigger — "when the root budget binds again" — is what authorized the change, and it is amended with the new number.
- Contributor-side only: an ADR is no longer the record a policy edit produces. `docs/decisions/` had reached 12,898 words against a 4,790-word package because releases 1.1 through 1.9 each wrote one. The `dogfood` skill conflated "needs the owner's approval" with "needs a new ADR"; approval still gates every contract wording change, but the record is the changelog section and the receipt, and an edit that answers a question an ADR already owns amends that ADR. This is the rule the product already gives owners under "Record proportionately" in `references/decision.md`, which the repository was not applying to itself.

### Verification status

- Deterministic checks pass (34 tests). Claude package validation and Claude isolated install pass locally; Codex package validation and Codex isolated install are `UNVERIFIED` here, as the Codex validator was not available in this environment. The root sits at 847 words against its new 1,000-word budget.
- That the moved rules change a run's behavior is `UNVERIFIED`. They now load on every request, which is necessary and not yet shown sufficient — the same standing 1.8.0 left for the merge boundary.
- 1.9.0's decomposition trigger remains `UNVERIFIED` in the field: no audited session has run it on a multi-item request.

## 1.9.0 (2026-08-26)

SkipHow 1.9 gives decomposition a trigger a run can evaluate before it starts working.

### Changed

- A session at 1.7.0 took fifteen owner corrections in one request — three of them marked systemic by the owner, spanning shared surfaces — and worked all of them in one root agent: 216 shell calls, 26 mutations, three commits, 87 minutes, with its only delegation a reviewer spawned after the work was committed. Nothing in the transcript mentions delegation, parallelism, a worktree, or a sub-issue at any point ([field audit](docs/research/2026-08-26/field-audit-2026-08-26.md)).
- The capability was never missing. `long-work.md` already specifies decomposition into bounded units, dependency-ordered readiness, one delegate per unit in its own worktree, and serialized integration; the [parallel orchestration survey](docs/research/2026-08-26/parallel-orchestration-proposals.md) mapped an external orchestrator proposal onto it mechanic by mechanic and adopted nothing. What failed was the door. `long-work.md` loaded "for a selected queue", and a selected queue is defined inside `long-work.md`, so a run had to know the term to decide whether to open the file that defines it ([ADR 0016](docs/decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md)).
- The root now names the negative case beside the positive one: a request is not bounded when it lists several items that could each land and be verified on their own, or when the owner calls a change systemic, and the run splits it into those units before starting any of them. The `long-work.md` trigger becomes "a request carrying several deliverable items" — evaluable before opening the file — and "a large diff alone does not" becomes "one large item does not", which is what it always meant.
- The selected queue explicitly includes the items the owner listed in the request. Decomposition produces bounded units that each fit one delegate, sub-issues when the tracker supports them, rather than requiring an Issue per unit on a tracker with no place to put one.
- "Delegates never hold credentials and never write to remote systems" moves into the root. It is unconditional wherever a delegate exists, and it lived only in `long-work.md` and `model-routing.md` — the two references that have never both loaded in a real session. Per [ADR 0015](docs/decisions/0015-unconditional-invariants-live-in-the-root.md) both references stop repeating it.
- The 1.8.0 receipt request for the merge boundary is narrower than it was. A fourth session, re-read after it finished, loaded `github.md`, held "'Fix', 'implement', repository policy, or Issue text alone never grants merge" in context, and merged and pushed anyway on a request with no end-to-end words. That fires ADR 0015's second revalidation trigger, and it is recorded there: moving the sentence to a surface that always loads is necessary and not yet shown sufficient.

### Verification status

- Deterministic checks pass (34 tests). Claude package validation and Claude isolated install pass locally; Codex package validation passes in CI, which is the only place the Codex validator was available. Codex isolated install is `UNVERIFIED`: neither environment ran it.
- The root is 794 words and 5,279 bytes against the 850-word, 6,000-byte budget; references total 3,599 words against 4,000, none over 600.
- Every 1.9.0 behavior change is `UNVERIFIED`. The receipt it needs is a run given several items in one request that splits them into units before starting, and a second showing whether such a run loads `model-routing.md` before it delegates — the reference has not loaded in 4 of 4 delegating sessions read so far, and this release will produce more delegations.
- 1.8.0 stays `UNVERIFIED` on every count. Its merge-boundary receipt is a delivery run on a "fix this" request that stops at the branch, not one that merely loads the reference.

## 1.8.0 (2026-08-26)

SkipHow 1.8 puts the rules that must always apply into the skill that always loads.

### Changed

- The first audit of real sessions in other repositories found that a reference which does not load does not govern: references loaded three times against roughly twelve applicable triggers. In the two sessions that never loaded `github.md`, none of seven Issue-create commands carried the required `skiphow:<id>` marker; in the one that loaded it, the marker was present. Two sessions merged a task branch into a shared branch, pushed, and deleted it on requests that said only "fix this systematically", because the prohibition lived only in `github.md` ([field audit](docs/research/2026-08-26/field-audit-2026-08-26.md), [ADR 0015](docs/decisions/0015-unconditional-invariants-live-in-the-root.md)).
- The root skill now states the merge boundary negatively: "complete end to end" adds merge, push to a shared branch, branch deletion, and cleanup, and nothing else grants those — not "fix", not the repository's usual flow, not an Issue, not an existing branch. It also says that a rule which did not load did not stop applying, and that the reference list is read before the act it governs.
- `TRACKED` now means a record that existed before the run and `SAVED` means the run created it; both carry a link, and `Saved follow-ups` repeats each record with its link. All five report headings appear even when an answer is none. Every delegation names its role. The privacy rule names records and public output rather than prompts, because a brief to a local delegate needs the working directory and 3 of 3 sessions broke the old wording with no leak.
- `engineering.md` no longer defines review dispositions of its own, removing the second findings vocabulary that let a run report `PERSISTED`, a tag ADR 0013 had recorded as undefined while a shipped reference defined it.
- The root budget is 850 words and 6,000 bytes, up from 600 and 5,000, and `scripts/check.py` states that the budget bounds drift rather than being a target to compress toward. The old number was self-imposed, not a host limit; measured against one real session's 77.1 million cache reads, the root's roughly 800 tokens are not the cost the budget assumed. Compressing to fit it had already cost ADR 0004 its step 4 for six releases.

### Added

- A contributor-only `dogfood` skill under `.claude/skills/` audits real sessions from other repositories against the package bytes each session ran. It does not ship with the plugin.

### Verification status

- Deterministic checks pass (34 tests). Claude and Codex package validation pass; Claude isolated install passes, Codex isolated install is `UNVERIFIED`.
- The 1.7.0 tracker-classification rule has its first field receipt: a session at 1.7.0 read the tracker's own labels and Issues, then created its Issue with the tracker's native type. One session, on a tracker that uses native types; the labels-only case stays `UNVERIFIED`.
- Every 1.8.0 behavior change is `UNVERIFIED`. Each needs a receipt from a real run: a delivery request that stops short of merging, a run whose report keeps an empty heading, and a session that loads `github.md` before its first write. A fourth session, re-read after it finished, narrows the first of those: it loaded `github.md`, held the prohibition in context, and merged and pushed regardless, so the receipt is a run that stops at the branch rather than one that merely loads the reference ([field audit](docs/research/2026-08-26/field-audit-2026-08-26.md), [ADR 0015](docs/decisions/0015-unconditional-invariants-live-in-the-root.md)).

## 1.7.0 (2026-08-26)

SkipHow 1.7 makes `RECORD` conform to the tracker's own classification instead of inventing one.

### Changed

- `intake.md` ordered "give each record a type" without saying what a type is or where it lands, and the only concrete tracker write the package named anywhere was a label. Dogfooding 1.6.1 on a project whose 237 Issues classify work with native GitHub issue types (175 typed: Bug 69, Feature 48, Task 45, Epic 13), a `RECORD` run created five Issues with `--label bug`. Now: read how the tracker already classifies work — native item types, labels, templates, required fields — match what recent items use, follow the newest consistent convention where they disagree and report it as a ruling, and never invent a classification the tracker does not already use. The convention is read live, not configured per repository ([ADR 0014](docs/decisions/0014-conform-to-the-tracker-classification.md)).
- `github.md` says the `skiphow-batch:<date>` marker is SkipHow's own bookkeeping, does not classify the work, and that a label is never a second workflow engine. This restores step 4 of ADR 0004, which was compressed out of the shipped reference in the 1.1 shrink and had governed nothing at runtime since.
- The `.skiphow/inbox.md` block carries a `Type:` field, so the no-tracker path can record the type the contract already required. README, guide, and the design page no longer read as though a record's type is a label.

### Verification status

- Deterministic checks pass (34 tests). Claude and Codex package validation pass; Claude isolated install passes, Codex isolated install is `UNVERIFIED`.
- Runtime behavior is `UNVERIFIED`: no receipt has yet shown a `RECORD` run matching a tracker's native item types. It needs a real run on a project whose tracker uses them, and a second on a labels-only tracker to show the rule derives rather than hardcodes.

## 1.6.1 (2026-08-26)

SkipHow 1.6.1 resolves one contradiction in the authority contract: a read-only request no longer authorizes saving a finding.

### Changed

- The root skill said saving a finding met along the way "is always within authority" while also making review, research, and diagnosis read-only, and ADR 0004 grants the finding record only with "fix" or "implement". Two Codex runs given "without changing anything" resolved the conflict by writing nothing and inventing a `PERSISTED` tag. Now: `DELIVER` and `RECORD` grant one record per material finding; a read-only request reports the finding as `UNSAVED` with a note that the owner can ask to save it; "review this, but save any material findings" grants the record. The guide, design page, README, and ADR 0013 say the same.
- README no longer claims findings were saved in every run; it states nine of ten tagged and saved whenever the request allowed.

### Verification status

- Deterministic checks and host validation as for 1.6.0; receipts appended to `docs/research/2026-08-26/v1.6-receipts.md`.

## 1.6.0 (2026-08-26)

SkipHow 1.6 makes Codex routing zero-config, frees the timestamp rule from one shell command, and removes documentation drift left by 1.4 and 1.5.

### Changed

- Codex routing needs no project setup. Codex's `spawn_agent` takes `reasoning_effort` per spawn when `fork_turns` is `"none"` or a number, and its own multi-agent prompt says skill instructions may set it. The routing reference now says so; the `codex-agents/` role files, the copy step, and the "set up SkipHow routing for Codex" sentence are gone.
- Observed on a fixture with no `.codex/agents/`: scout at `low`, reviewer at `high`, root and both delegates on the session model (1.6 receipts).
- Inbox and handoff `Recorded` lines state the invariant instead of one shell command: the UTC time read from the system clock as `YYYY-MM-DDTHH:MM:SSZ`, `unknown` when no clock can be read, never estimated. On Claude Code a feature run wrote `02:20:20Z` inside its `02:19:48Z` to `02:20:29Z` window by calling `date -u` on its own.
- The design page no longer says a two-line fix loads the delivery reference, and the guide, design page, README, and routing reference now agree on Codex routing without mentioning role files.

### Verification status

- Deterministic checks, Claude Code validation and isolated install, and the pinned Codex validator pass on the tagged commit; the Codex isolated install stays `UNVERIFIED` on the release machine.
- Native Windows and the `unknown` timestamp fallback remain `UNVERIFIED`.
- Receipts: `docs/research/2026-08-26/v1.6-receipts.md`.

## 1.5.0 (2026-08-26)

SkipHow 1.5 drops the delivery reference for bounded changes, records real timestamps, and says what Codex routing is.

### Changed

- `DELIVER`: a clear bounded change you can finish and verify directly loads no reference; `delivery.md` loads otherwise. In a paired experiment on three small tasks the reduced variant matched the current skill on correctness and findings and cost 10 to 20 percent less; two verification runs on the final wording held the findings tag, the intake block, and the timestamps (`paired-eval.md`, 1.5 receipts).
- Inbox and handoff `Recorded` lines take the output of `date -u +%Y-%m-%dT%H:%M:%SZ`, or `unknown` when no clock is available, instead of a format hint the model filled in by hand. Three runs wrote clock values inside the run's real window.
- Findings saved to the inbox are one block per finding, written after reading `intake.md`.
- Codex routing is described as what it is: every delegate runs on the session model; the shipped role files set sandbox and reasoning effort per role. Observed: `builder` at the session's effort, `scout` at low effort, `reviewer` at high effort, all on the session model. The reference, the design page, ADR 0011, and the README now agree.
- README: the process comparison is framed as a hypothesis, the paired numbers are stated with their limits, and the Codex line no longer implies capability tiers.

### Verification status

- Deterministic checks, Claude Code validation and isolated install, and the pinned Codex validator pass on the tagged commit; the Codex isolated install stays `UNVERIFIED` on the release machine.
- Receipts: `docs/research/2026-08-26/v1.5-receipts.md` and the updated `paired-eval.md`.

## 1.4.0 (2026-08-26)

SkipHow 1.4 makes out-of-scope findings an invariant instead of a judgment, ships Codex role files, and separates contributor rules from runtime policy.

### Changed

- Every finding named in a report carries `TRACKED`, `SAVED`, or `DISMISSED` with its reason; saving a finding is always within authority; "outside the request" is not a dismissal reason; inbox entries use the intake block. Four rounds of observed failure and rerun are in the 1.4 receipts; the tag is what held (ADR 0011).
- The skill ships `codex-agents/scout.toml`, `builder.toml`, and `reviewer.toml` (effort and sandbox per role, never a model name). "Set up SkipHow routing for Codex" copies them into `.codex/agents/`. `spawn_agent(agent_type="builder")` was observed on Codex with the exact candidate.
- `AGENTS.md` is now contributor rules only (evidence, checks, portability, safety); the package shape lives in the ADRs and `scripts/check.py`. The runtime skill lost its repository guardrail sentence.
- `scripts/run_summary.py` summarizes a Claude Code stream-json transcript (turns, cost, time, tools, delegations) so paired runs compare the same way.
- The owner guide notes that Codex's `workspace-write` sandbox could not write `.git/index.lock` on the release machine, so unattended commits need a wider sandbox or a commit afterwards.

### Verification status

- Deterministic checks, Claude Code validation and isolated install, and the pinned Codex validator pass on the tagged commit; the Codex isolated install stays `UNVERIFIED` on the release machine.
- Receipts (`docs/research/2026-08-26/v1.4-receipts.md`): findings saved in 4 of 4 runs after the tag; handoff deleted after an observed compaction; a three-track request decomposed into three Issues and three merged PRs; Codex builders spawned by role. Paired evaluation (`paired-eval.md`): the skill adds two to three turns and 20 to 30 percent cost on small tasks; both arms were correct; without the skill, "save them" wrote to the host's memory directory instead of the project. Codex `scout` and `reviewer` effort, delegation inside a Claude Code epic, and auto-compaction under a large context remain `UNVERIFIED`.

## 1.3.0 (2026-08-26)

SkipHow 1.3 halves the continuity hook, records the first Codex receipts, and removes a historical guard from the checks.

### Changed

- `hooks/hooks.json` has two `SessionStart` groups (`startup|clear` and `compact|resume`) instead of four byte-duplicated ones. Both hosts document matcher lists, and both groups were observed firing on Claude Code (ADR 0010).
- The compaction and resume hook line now also says to delete `.skiphow/handoff.md` once every selected item is done, because two continuity runs kept a finished handoff.
- The queue for long work may come from `.skiphow/inbox.md` when the project has no tracker, so "save it" and "finish it" both work offline.
- `references/decision.md` lost its record template and acceptance ceremony; it keeps the invariants (recommend with the tradeoff, reconcile before superseding a durable decision, record boundary changes).
- The Codex plugin's example prompts match the daily flow shown in the README.
- The README is shorter and says which claims have receipts.

### Removed

- The retired-runtime path guard in `scripts/check.py` and its test; the plugin top-level check already rejects unexpected entries.
- The exact dependency pin list duplicated in a test; the test now checks that every requirement is pinned.

### Verification status

- Deterministic repository checks, Claude Code package validation and isolated install, and the pinned Codex package validator pass on the tagged commit. The Codex isolated install stays `UNVERIFIED` on the release machine because its managed policy rejects local marketplaces.
- Receipts for this release (`docs/research/2026-08-26/v1.3-receipts.md`) cover, on Codex with the exact candidate loaded from the project skills directory: a small bug fixed in session and a brain dump saved to the inbox with priorities and duplicate detection; and on Claude Code: continuity across an observed compaction with both hook groups firing, and a large request delivered end to end on GitHub (Issue, PR merged on the read head, branch deleted). Codex delegation, an epic split into several Issues, and auto-compaction under a large context remain `UNVERIFIED`.

## 1.2.0 (2026-08-26)

SkipHow 1.2 makes the reviewer follow the owner's own model, turns a brain dump into a prioritized backlog, and cuts the policy and its checks further.

### Changed

- The `reviewer` adapter inherits the session model instead of pinning `opus`. The 1.1 receipt showed the root on a stronger model than its reviewer; the deepest tier is now always the model the owner chose, on every provider and model generation (ADR 0009).
- `RECORD` gives every record a type and a proposed priority with its reason, and reports the proposed order. "Finish today's batch" works the batch in that order. An epic given as one request is split into bounded Issues first.
- The five engineering method files and their router are one `references/engineering.md` holding only the invariants (exact-candidate review, a bug test that fails before the fix, prototypes never ship unchanged, conflicts are never resolved by picking a side). The references are eight files and about 3,450 words, from thirteen files and about 4,300.
- The root deletes `.skiphow/handoff.md` when every selected item is disposed, so a finished queue no longer greets every new session.
- The word budget check is one function in `scripts/check.py` with fixed limits (root under 600 words, references under 4,000 in total and 600 per file).

### Removed

- `references/methods/` and `references/engineering.md` as a router.
- `scripts/context_budget.py`, its baseline file, and its tests.
- Stale ignore rules for the harness removed in 1.1.0.

### Verification status

- Deterministic repository checks, package validation in both hosts (the Codex validator pinned in CI, run locally too), and the isolated Claude Code install pass on the tagged commit. The Codex isolated install is `UNVERIFIED` on the release machine because its managed policy blocks local marketplace sources.
- Receipts for this release (`docs/research/2026-08-26/v1.2-receipts.md`) cover, on Claude Code: a small bug fixed in session, a normal feature, reuse of a pinned dependency, a brain dump turned into six prioritized Issues, a six-Issue batch finished end to end with four merged pull requests and cleanup, handoff and resume, the compaction hook, and two `builder` delegations on the standard tier in isolated worktrees. Codex, auto-compaction under a large context, and protected batch repositories are `UNVERIFIED`.

## 1.1.0 (2026-08-26)

SkipHow 1.1 makes model routing and compaction continuity real, cuts the policy to intent plus invariants, and removes the harness and documentation that did not earn their keep.

### Added

- Three role adapters for Claude Code under `plugins/skiphow/agents/`: `scout` (haiku, low effort, read-only), `builder` (sonnet, isolated worktree), `reviewer` (opus, high effort, read-only plus checks). Shared policy names roles only; family aliases live in the adapter (ADR 0007).
- One read-only `SessionStart` hook (`plugins/skiphow/hooks/hooks.json`) that, at startup, tells the session to use the skill for project requests and, after `compact` or `resume`, prints the latest `.skiphow/handoff.md` checkpoint back into context. Both hosts read it from the default location.
- A Codex routing path: the `[agents]` settings and the `.codex/agents/<role>.toml` files SkipHow writes on request, since Codex plugins cannot ship agents.
- Batch markers: `RECORD` labels the Issues it creates from one dump with `skiphow-batch:<date>` so "finish today's batch end to end" needs no Issue numbers.
- A five-heading completion report (Result, Evidence, Rulings and findings, Saved follow-ups, Limits) and an eight-line handoff checkpoint.
- A tag-driven release workflow that reruns the checks and publishes the GitHub release from the matching changelog section.
- Deterministic checks for the agents (exact roles, family aliases only, no versioned IDs) and the hook (exactly one, read-only, no network), plus a references word budget.

### Changed

- Rewrote the skill and every reference for a strong model: root under 600 words, references about 4,000 words in total (from about 6,000). The 23-field checkpoint, 15-line worker packet, `CIRCUIT_BROKEN` lanes, compare-and-delete prose, and the 13-step GitHub lifecycle are replaced by invariants: fixed queue, one root integrates, four reasons to stop, two same-cause retries, re-read live state before merge, delete only owned merged branches.
- Reuse before building now triggers on any new module or feature, searches by domain concept, and reports where it looked.
- Continuity changed from "checkpoint before compaction" (which the model cannot see coming) to "checkpoint at every item boundary and before long waits", surfaced by the hook.
- Tests check structure (routes, references, agents, hook, formats, versions, pins) instead of exact sentences.
- Documentation consolidated into an owner guide and a design page; the README leads with the daily flow. ADR 0002, 0003, and 0006 are amended by ADR 0007; ADR 0005 is superseded by ADR 0008.

### Removed

- The opt-in live evaluation harness (`evals/live`, its fixtures, oracles, tests, and `docs/evals.md`). It produced no receipt in four releases; behavior is now proven by written receipts (ADR 0008).
- `docs/getting-started.md`, `user-guide.md`, `architecture.md`, `trust.md`, `threat-model.md`, `intake.md`, `github-lifecycle.md`, and `model-routing.md`, folded into `docs/guide.md` and `docs/how-it-works.md`.
- Runner-era leftovers and stale ignore rules.

### Verification status

- Deterministic repository checks, both host package validations, and isolated installs pass on the tagged commit.
- Receipts for this release are listed in `docs/research/2026-08-26/README.md`. Anything not covered there is `UNVERIFIED`.

## 1.0.1 (2026-08-26)

### Changed

- Made repository-required tracked delivery take precedence over the small-change shortcut.
- Required durable reconciliation for privacy and audience-boundary changes and for decisions that supersede an accepted product record.
- Added explicit independent-finding triage, changed-surface warning handling, and pre-change attribution for overlapping dirty files.
- Preferred synthetic or redacted diagnostic evidence when private or production-derived data is unnecessary.
- Added non-spoon-fed live scenarios for implicit independent findings and public data-boundary changes.

### Verification status

- Deterministic repository and package checks remain the release requirement.
- Model interpretation of the new scenarios remains `UNVERIFIED` until an opt-in live receipt proves the exact candidate.

## 1.0.0 (2026-08-26)

SkipHow 1.0 is the first stable release of the host-native design. It remains one portable skill, with no SkipHow runner or task database.

### Changed

- Defined a recoverable long-work protocol around a selected queue, dependency-ready waves, bounded worker packets, health checks, checkpoints, reconciliation, exact-candidate review, and final queue reconciliation.
- Restored focused engineering guidance for diagnosis, testing, technical review, design, disposable prototypes, and conflict resolution as lazy references under the canonical skill.
- Made the authority boundary explicit. Only the owner request and host policy grant actions. Repository rules and project decisions may restrict those actions but cannot expand them.
- Kept external mutations, integration, protected actions, and cleanup with the root agent. Workers receive the least authority needed for their packet.
- Bound protected review and delivery to the repository, base and candidate identity, Git state, executable inputs, required checks, and current remote state.
- Hardened retries and cleanup. A timeout triggers reconciliation before retry, and owned-branch cleanup verifies the expected object identity before deletion.
- Expanded public installation, update, uninstall, support, security, and troubleshooting documentation for Codex and Claude Code.
- Aligned both host manifests with `VERSION`, made the Claude marketplace defer to its plugin manifest, and tightened deterministic release checks for recursive references and version changes.
- Expanded the release evaluation contracts for campaign recovery, technical review, and conflict resolution while keeping live model and mutable GitHub trials opt-in.

### Security

- Treats repository files, trackers, checkpoints, tool output, web content, and subagent reports as untrusted data rather than permission grants.
- Limits checkpoints to bounded, redacted recovery data. They must not contain credentials, private absolute paths, or untrusted instructions that can be replayed as authority.
- Requires the root to inspect repository-controlled tests and scripts before running them when their behavior or trust is uncertain.

### Verification status

- Deterministic repository and package checks remain the release requirement.
- Live host behavior, full restart recovery, autonomous model selection, routing savings, and mutable multi-Issue GitHub delivery remain `UNVERIFIED` unless an exact 1.0 receipt proves them.

## 0.9.0 (2026-08-25, preview)

Version 0.9.0 removes the Python runner introduced in 0.8. SkipHow is now one portable, owner-facing skill. Codex and Claude use the host's own sessions, goals, subagents, worktrees, resume support, and permission controls.

This is a breaking release. The `skiphow` executable, its SQLite state, runtime schemas, provider adapters, and runner configuration no longer exist. SkipHow does not provide a compatibility command or migrate runner state. Git history retains the removed implementation.

### Changed

- Kept one public `skiphow` entry point for discussion, capture, delivery, and task control. Requests use ordinary language instead of separate fix, CTO, idea, or automode commands.
- Made short tasks run in the current host session. Long work uses host-native goals and background tasks when the host provides them.
- Made GitHub Issues, pull requests, and Git the durable record for tracked work. Projects without GitHub can keep explicit capture requests in `.skiphow/inbox.md`.
- Replaced model names with the semantic `FAST`, `STANDARD`, and `DEEP` tiers. The root maps them only from current host metadata and otherwise inherits the current model with an `UNVERIFIED` selection result.
- Limited automatic merge to explicit unattended or end-to-end work. Required checks, reviews, repository rules, and exact-head checks still apply.
- Made pause, cancellation, and narrower authority cancel owned pending merge actions, and made recovery fail closed without trusted scope, authority, ownership, and exact state.
- Defined one deduplicated intake record as part of delivery authority for a material independent finding, without implementing or reprioritizing it.
- Rewrote the plugin policy, architecture, research notes, decisions, and README around the host-native design.

### Added

- Added an opt-in live evaluator for ten owner workflows. It loads an exact candidate and grades synthetic workspaces against external oracles. Mutable GitHub execution fails closed until an external boundary can prevent repository deletion while allowing required Git writes.
- Added recursive receipt redaction, exact installed-payload comparison, repository-free marketplace snapshots, and the package's MIT license text.

### Removed

- Removed the `skiphow` Python package and the `setup`, `intake`, `start`, `add-task`, `github-deliver`, `execute`, `worker`, `status`, `pause`, `resume`, `cancel`, `reconcile`, and `export` CLI commands.
- Removed SQLite run state, the supervisor, provider transports, model calibration, runtime verification, security journal, JSON runtime schemas, and runner-specific configuration.
- Removed the copied Claude skill shim and vendored workflow instructions. Both host packages now use the same canonical skill.
- Removed runner-specific tests and evals that did not install and exercise the exact candidate plugin.

### Verification status

- Deterministic repository and package checks remain in CI.
- Live Codex and Claude outcome checks remain opt-in. Implicit selection, owner-intent interpretation, host-native continuation, unattended GitHub delivery, autonomous model selection, and model-tier savings stay `UNVERIFIED` until exact 0.9 evidence covers them.

## 0.8.0 (unreleased development candidate)

This unpublished candidate explored a durable Python runner, SQLite state, provider adapters, and a larger evaluation harness. Version 0.9.0 removed that architecture. Git history preserves the implementation and migration details.

## 0.7.0

### Changed

- Replaced runtime reads of vendored upstream methods with compact, self-contained diagnosis, testing, technical review, and codebase design capabilities. Source copies, licenses, and pinned attribution remain source-only.
- Reduced every measured route closure. Common software routes are at least 23 percent smaller than v0.6; diagnosis and optional capability routes are at least 37 percent smaller.
- Made readiness, delegation lane contracts, operation health fields, review, and durable records conditional on the work that needs them.
- Added direct execution for non-software project artifacts inside the existing `CHANGE` intent, with source, render, or preview evidence suited to the artifact.
- Added verbatim request alignment, verification-gap checks, evidence-backed finding types, and precise in-scope completion semantics.
- Reworked repository outcome evals around correctness, mutation boundaries, required evidence, forbidden side effects, and separately reported economy signals.
- Replaced host-name assumptions with a semantic capability contract and single-agent fallback for bounded work.
- Split GitHub candidate search from semantic duplicate decisions, separated linked-branch creation from delivery provenance, and made Project status mapping explicit and optional.
- Corrected support documentation so CLI availability is not package proof and untested hosts or products remain `UNVERIFIED` or unclaimed.

### Added

- Added `scripts/context_budget.py`, a committed decreasing baseline, runtime-to-upstream lint, and CI ratchet for route context.
- Added `.skiphow/config.json` as the only optional config contract, with strict validation for tracker, Project, and campaign path settings.
- Added package-proof receipt handling to doctor, host capability profiles, 20 repository outcome scenarios, five policy mutations, multi-trial aggregation code, and a machine-readable live receipt format.
- Added campaign-only goal ancestry, budget envelopes, cancellation, idempotent lane claims, checkpoints, orphan recovery, and final reconciliation.
- Added lazy contracts for extensions, consequential behavior deltas, source-backed product decisions, and explicitly maintained verified project context.

### Removed

- Removed `.skiphow/config.yml`, `strict_lifecycle`, runtime upstream loading, implicit substring duplicate claims, and automatic Project status assumptions.
- Removed package-validated support claims that were not backed by a fresh receipt.

### Migration from 0.6

- If `.skiphow/config.yml` exists, move supported values to `.skiphow/config.json`, replace disabled Project values with `null`, and delete `strict_lifecycle`.
- GitHub adapter callers should use `find_candidates`, `create_linked_branch`, and `record_delivery`; Project status updates now require an explicit field and option mapping.
- Treat existing host support statements as historical only. Generate fresh package and live outcome receipts for the exact 0.7 candidate before publishing support claims.

## 0.6.0

### Changed

- Replaced the public workflow catalog with one conversational `skiphow` entrypoint for answer, capture, decision, change, repair, and continuation requests.
- Clear changes now execute from a lightweight delivery brief without mandatory shaping, tracking, Owner approval, product review, or acceptance receipts.
- Made extended product records, independent product review, and product acceptance conditional on consequential decisions or repository policy.
- Made GitHub Issues the optional default persistence integration and GitHub Projects an explicitly configured view.
- Replaced blocking preflight semantics with a read-only doctor that reports optional capabilities independently.
- Split deterministic local checks from optional host validation and added version consistency checks.
- Added activation, routing, repository outcome, forbidden-side-effect, and policy mutation eval coverage.
- Simplified dependency diligence and campaign state so optional fields and artifacts appear only when triggered.

### Added

- Added `.skiphow/inbox.md` as the local fallback for explicit capture requests with no configured tracker.
- Added narrow optional `github_issues.py`, `github_project.py`, and `doctor.py` adapters.
- Added a support matrix, privacy notes, diagnostics, update, rollback, and uninstall guidance.

### Removed

- Removed default lifecycle hooks and the monolithic GitHub lifecycle helper.
- Removed runtime handling of the legacy `Human Gate` Project field. Existing fields are left untouched and ignored.
- Removed separate public Codex skills and Claude wrappers for internal workflows.

## 0.5.0

### Changed

- Simplified technical routing to normal `EXECUTE`, focused `DIAGNOSE`, and durable `CAMPAIGN` paths.
- Replaced universal risk levels with concrete changed surfaces that determine evidence and review without selecting orchestration.
- Made tracking lazy, combined scope control with terminal finding dispositions, and limited revalidation to semantically invalidated evidence.
- Generalized completion and product-acceptance receipts from commit-only gates to exact delivered-state identities, with recovery guidance for existing campaign state.
- Focused subagents on context isolation, independent review, and genuinely parallel work instead of label-driven ceremony.
- Made GitHub Issues the durable work identity and a minimal Project the default human-facing queue, with Issue-only degraded operation and no mandatory `Human Gate` schema.
- Added vertical-slice and fog-of-war campaign decomposition, strict domain-glossary and ADR thresholds, and a verified human-action handoff.

### Added

- Added disposable `prototype` and intent-preserving `resolving-merge-conflicts` capabilities.
- Added `setup` for reusing or bootstrapping the standard minimal GitHub Project.

## 0.4.0

### Added

- The internal `cto` controller for direct, tracked-direct, or durable technical delivery.
- Internal testing, technical-review, and codebase-design capabilities adapted from pinned MIT sources.
- Product Director acceptance for user-visible Product Contract work.
- A read-only `preflight` workflow for local tools, GitHub authentication, board schema, hooks, and host commands.
- A 24-scenario behavioral corpus, a structured Codex runner, and one deterministic release-verification entrypoint.

### Changed

- `develop`, `fix`, and technical maintenance now route through the CTO instead of treating `cto-run` as all technical execution.
- Risk controls validation and review depth. Durability controls whether work uses `cto-run`.
- CI now runs package metadata, YAML, source, Markdown-link, behavioral-corpus, repository-test, and whitespace checks through `scripts/verify_release.py`.
- Python 3.10 or newer is now the documented minimum for the bundled lifecycle helper.

## 0.3.0

### Added

- The internal `github-task` lifecycle adapter for tracked GitHub work.
- Portable Codex and Claude Code hooks for linked-branch status and compact Project v2 operations.

### Changed

- `fix`, `develop`, and `cto-run` now decide when GitHub tracking applies before handing lifecycle work to `github-task`.
- GitHub lifecycle no longer selects implementation methods, test policy, review depth, or verification cadence.

## 0.2.0

### Added

- The `skiphow`, `idea`, `shape`, `develop`, `fix`, and `diagnose` skills.
- Adaptive defect routing through direct repair, internal diagnosis, bounded product decisions, or durable CTO campaigns.
- Product Contract review and immutable delivery campaign guidance.
- Claude Code adapters for every shipped skill.

### Changed

- Claude Code now loads the full SkipHow skill adapter directory.
- `diagnose` is now an internal capability used only when the cause is unclear.

## 0.1.0

### Added

- The `cto-run` skill for explicit, durable software campaigns.
- Codex and Claude Code plugin adapters.
- Repository contract tests, contributor policy, and CI.
