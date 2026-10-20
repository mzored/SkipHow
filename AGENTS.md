# Repository instructions

These are contributor rules for developing SkipHow. Runtime behavior lives in `plugins/skiphow/`, the package under test. Do not let an installed SkipHow plugin govern work on this repository.

## Repository map

- `plugins/skiphow/`: the installable package.
- `docs/`: current user, product, and evidence documents.
- `evals/`: evaluation data, fixtures, and retained receipts.
- `tests/`: offline deterministic tests.
- `scripts/`: contributor checks and capture, grading, and privacy tools.
- `site/`: the static website the release workflow publishes.
- `.github/`: contribution policy, issue templates, and CI.
- `.claude/skills/`: the dogfood skill, contributor tooling outside the package.

## Product direction

[The owner-outcome contract](docs/outcome-contract.md) is the canonical product objective. The implementation is one accountable CTO kernel, optional workflow skills, and shared internal references. A workflow sets the owner's work pattern and leaves technical supervision with the agent. Preserve autonomous technical judgment, effort proportional to the request, and the least total cost that reliably delivers the outcomes. Evidence may justify native host bindings or a thin adapter.

Keep universal runtime policy in the kernel as outcomes, authority boundaries, and non-negotiable invariants. Everything else is optional guidance, consulted when worth its cost. A module must cover one distinct failure domain, show a reason to consult it without being opened, hold no critical invariant missing from the kernel, duplicate no other module's rule, and repay its permanent discovery and maintenance cost. Modules are not routes, commands, roles, stages, or an owner-operated chain. Leave sequencing, tools, decomposition, and implementation to the agent unless evidence shows its judgment is unreliable. Audit briefs, checklists, transcripts, and one-off preferences are evidence for their question, not standing requirements.

## Changing the runtime contract

Change the shipped instructions to fix an observed defect, protect a high-risk boundary, or implement an explicitly requested product capability. An owner-selected workflow may prescribe its defining behavior without making it universal. One run can show wording is missing, ambiguous, or contradictory. It cannot show agents generally need a new procedure.

Judge additions, removals, and kept complexity by the outcome contract and total cost. Before a material removal, name the useful behavior, its surviving execution path, and the acceptance check. Missing behavioral evidence is uncertainty, not proof that a required responsibility is unneeded. Remove duplicates and contradictions without a paid experiment when inspection settles them. Outside an explicitly requested optional workflow, add a mandatory step, role, gate, dependency, or persistent state only when evidence shows capable agents cannot reliably infer the behavior and the benefit pays its ongoing cost. Check each change for lost responsibility or autonomy, extra turns, maintenance cost, and provider assumptions.

`scripts/check.py` caps each runtime Markdown file in raw characters so a failing shell read with a short error line shows it whole. Claude Code still cuts failing output to about 10,000 characters, and agents read skill files with chained shell commands. The kernel sits at the cap by design, so an addition displaces equal text. Method belongs in the playbook that opens at the act. When the headroom lint names a playbook, tighten it in the change that brought it there and keep its headings and responsibilities, so the next addition need not cut unrelated guidance.

## Reviewing a change to the instructions

This governs a contributor acting on a review of their own change, not the reviewer. Prose always admits another wording, so a review free to propose one never ends. Weigh findings as evidence, not a work list, and confirm each against the file first. A reviewer that cannot point at the defect is reporting taste.

A finding qualifies when it names:

- a factual error in a number, in what a file says, or in how a host behaves;
- a contradiction with another shipped sentence;
- a module whose reason to consult it is not recognizable unopened;
- a claim presented as demonstrated that no receipt supports;
- a mandatory step, gate, or persistent state added without the evidence this file requires;
- an authority, boundary, or portability error.

Fix what qualifies within the change's scope and record it. A rephrasing that changes no behavior, a hedging preference, or a clarity request that names nothing broken does not qualify. Say so and leave the sentence. Confidence and list length are not evidence. Stop when a round returns no qualifying finding. Open no further round, and do not re-review wording that survived one. The observed defect is the completion condition.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance. Read prior decisions for earlier constraints and settled analysis. Reopen a decision when host behavior, model evidence, product goals, security boundaries, or maintenance cost materially changes its premises.

Only deliberate receipts prove model behavior: real runs under the host's own permission and budget controls. A receipt varies only the package, using a throwaway fixture repository, a session with only the candidate package and host built-ins, and the same prompt on both sides. Isolate Codex by pointing its home and the OS home at a scratch location, because it also reads a host-agnostic user skill directory its home setting misses. Isolate Claude by disabling every setting source and passing the package as a session plugin, which keeps authentication. Prove isolation with a control run, confirmed in the transcript and not by asking the model, before trusting anything built on it. Even with setting sources disabled, a session can still read maintainer instruction files by shell, so search each transcript for them and for the package. Run the failing case before the change and after it. A run showing only the new behavior proves the wording allows it, not that it caused it.

Keep receipts small. The 2.16.1 pass spent forty sessions, fifty-one invocations, $165, and nearly five hours on one yes-or-no question that four sessions under six dollars answered. Name the observable first, and stop each session when it lands, not when the task ends. If the observable is behavior at dispatch, do not pay for delegates to finish, because that buys nothing and costs most of the run. If it is what they return, let them. Read what earlier receipts recorded about the prompt shape that produces the behavior. Pilot one session per arm, run one more per arm, and stop. Run a third only when the two disagree. Keep one fixture. If the pilot never shows the behavior, fix the prompt from the record instead of running another batch. Set a per-session spending limit and a receipt ceiling, and cap sessions in flight. Give each run its own fixture directory and log, because shared ones destroy each other's evidence. Read transcript write times before calling a run stuck, because a root blocked on a delegate looks like a hang.

`docs/evidence.md` defines the claim labels and what each claim needs. A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

The `evals/` corpus is arm-aware. Each case states what holds in every arm and what each arm may, must, and must not do. No case may require a package-only event from an arm without the package, and the corpus tests reject a case no arm could satisfy. A paid run needs the owner's authorization, stays within the corpus's recorded limits, and never runs from CI. A passing corpus test moves nothing toward `Observed`.

## Documentation

[The README](README.md#documentation) indexes the current documents. `docs/decisions.md` indexes live decisions and their premises, and links historical rationale in immutable snapshots as rebuttable context, not a veto. `docs/evidence.md` summarizes claims with durable source links. Add no research file per run or release.

Documentation describes the current state. Per-release motivation, field traces, and review rounds go in `CHANGELOG.md`, and git history keeps earlier text. A release edits `docs/decisions.md` only when a decision, its premise, or its reopen condition changes, and `docs/evidence.md` only when a claim's status changes or a new receipt lands. Neither file carries a per-release narrative or a version log. Keep `docs/` free of restatements of the shipped package, and link the shipped file instead.

## Writing instructions for the model

The shipped text and every delegate brief follow one prompt standard. State the goal, the context that settles it, the authority granted, the constraints, what success looks like, and what to report, in that order, in plain declarative sentences. In a long prompt, put durable material first and the request last. Prefer a positive instruction to a prohibition, with its reason where one exists. Use an example only where the shape is otherwise ambiguous. Omit steps a capable model would infer, and name the observable, not the process. Ask for reasoning only where the task warrants it, and route model and effort by consequence and complexity, not a fixed tier. Each sentence should carry an outcome, boundary, or useful method. Cut redundant wording but keep each responsibility's execution path. Do not assert how models in general behave without a source.

## Checks

`scripts/check.py` and `scripts/check_hosts.py` run through `agent-verify` when that optional host capability is on PATH. It validates a live inherited grant or queues the whole check before any execution timeout starts, keeps admission status visible, and stops the check on an adapter error. Other hosts run the same portable checks directly. The integration adds no dependency to the shipped plugin.

Install the pins with `python -m pip install -r requirements-dev.txt`. The checks install nothing and stop on an interpreter missing a pin. Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. `tests/conftest.py` keeps a direct `pytest tests` run from writing bytecode into `plugins/skiphow/`, whose every file the package identity hashes.

Completion needs one full `python scripts/check.py` result and one clean `git diff --check` on the final candidate. After bounded failures, repair them and rerun only the affected signals when inspection proves no other input changed. Those passes and the full result are the completion evidence. Bind each result to the code, dependencies, configuration, and environment it covered, and reuse it while they stay equivalent. A commit, clean merge, tag, or release stage alone does not invalidate it. After integration, use revision-bound CI or establish relevant tree equivalence, and rerun only checks whose inputs changed.

When a change affects manifest shape, package layout, installation, or host validation, also run `python scripts/check_hosts.py`. It reports one row per host capability. Report an unavailable host as `UNVERIFIED`. A version value or new runtime prose in an unchanged package structure does not alone require a clean-install smoke.

`scripts/check.py` validates the required CTO skill, sibling workflow links to it, reachable modules and resources, the safety shape of any shipped hook, aligned versions, and portability boundaries such as personal paths and versioned model IDs. When those invariants change, change the check and `docs/decisions.md` together.

Assertions on a package or host contract, a security or release invariant, or the corpus's semantic validity fail the run. An editorial or layout preference is at most a non-blocking lint. Delete any assumption about the current shape unless it becomes a stated contract with a reason. Do not pin a marketing sentence, a method roster or count, a role set, a hook matcher topology, a site presentation detail, or a prose budget without a measured limit.

## Versioning and releases

Follow Semantic Versioning 2.0.0. The public surface is the runtime contract, not the file layout: owner-visible behavior, authority boundaries, default side effects, the public skill name and description, and any format a project keeps. `PATCH` is a repository, documentation, or wording change that keeps the promised behavior. `MINOR` is an opt-in capability, module, or behavior compatible with installed projects. `MAJOR` changes the owner interface, an authority boundary, or a default side effect with no safe path for installed projects. Pick the number once the change is complete and its compatibility known. Do not reserve a major version while planning.

Release one coherent, verified change set at a time. Bump `VERSION` and both manifests once, at the start of the release branch, and keep that number through it. Related work accumulates there, not as a series of releases on `main`. Never edit or re-tag a released version. Claim a material change in model behavior only after receipts.

Keep one immutable release candidate. Run focused checks while it changes, then one final local gate and one independent review at the depth the change warrants. Pull-request and `main` CI supply their own revision-bound evidence. After CI passes the integrated revision, do not repeat the local gate before tagging. Recheck only properties the candidate evidence missed, and verify the release and site at their destinations. Run model sessions and clean-install receipts only when the claim or a changed delivery mechanism needs them, never because work reached a later stage.

Every release publishes the compact validation matrix, one row per capability: deterministic package gate, Codex and Claude schema validation, clean install on each host, explicit invocation, implicit activation, continuity, and behavioral suite. Each row reads `PASS`, `FAIL`, `UNVERIFIED`, or `Observed`. The behavioral row points at `docs/evidence.md`, and CI never implies it. A skipped check stays visible as `UNVERIFIED`, never folded into a green aggregate.

## Portability and safety

Keep personal paths, home-directory assumptions, credentials, telemetry, and network calls out of the package and its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
