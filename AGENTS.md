# Repository instructions

These are contributor rules for developing SkipHow. They do not describe how SkipHow behaves at runtime; that lives in `plugins/skiphow/` and is the thing under test here. Do not use an installed SkipHow plugin to govern work on this repository.

## Product direction

Treat [the owner-outcome contract](docs/outcome-contract.md) as the canonical product objective. The README explains that contract to users. The current implementation is one plain-language owner skill backed by a governing kernel and optional modules. Preserve autonomous technical judgment, effort proportional to the request, and the least total cost that reliably delivers the required outcomes. Native host bindings or a thin adapter may change this implementation where evidence justifies them.

Keep universal runtime policy in the kernel as outcomes, authority boundaries, and non-negotiable invariants. Everything else is optional guidance, consulted when the work makes it worth its cost. A module exists only where it covers one distinct failure domain, gives a reason to consult it recognizable without opening it, holds no critical invariant absent from the kernel, duplicates no rule another module owns, and repays the permanent discovery and maintenance cost of a separate file. Those criteria are drawn from the 1.8.0 field audit, which measured references loading three times against roughly twelve applicable triggers while the rules in the unopened files governed nothing. Modules are not routes, commands, roles, stages, or an owner-operated chain. Leave sequencing, tools, decomposition, and implementation to the agent unless evidence shows that judgment is unreliable. Audit briefs, checklists, past transcripts, and one-off preferences are evidence for the question they examine; they are not standing product requirements.

## Changing the runtime contract

Change the shipped instructions to fix an observed defect or protect a high-risk boundary, not to describe an ideal execution in full. One run can prove that wording is missing, ambiguous, or contradictory. It cannot prove that agents generally need a new procedure.

Evaluate additions, removals, and retained complexity against the same outcome contract and total cost. For a material removal, identify the useful behavior, its surviving execution path, and the acceptance check. Missing behavioral evidence is uncertainty, not evidence that a required responsibility is unnecessary. Remove duplicates and contradictions without a paid experiment when inspection settles the result. Add a mandatory step, role, gate, dependency, or persistent state only when evidence shows that capable agents cannot reliably infer the needed behavior and the benefit justifies its ongoing cost. Review each change for lost responsibility, autonomy, extra turns, maintenance cost, and provider assumptions.

## Reviewing a change to the instructions

This is for the contributor acting on a review of their own change, not for the reviewer producing one. The shipped contract is prose, so a reviewer can always propose a different wording, and a review that is allowed to do so never ends. Treat what comes back as evidence to weigh, not a list to work through, and confirm every finding against the file yourself before acting on it. A reviewer that cannot point at the defect is reporting taste.

A finding qualifies when it names one of these: a factual error, including a number, a claim about what a file says, or a claim about how a host behaves; a contradiction with another shipped sentence; a module whose reason to consult it cannot be recognized without opening it; a claim presented as demonstrated that no receipt supports; a mandatory step, gate, or persistent state added without the evidence this file requires for one; or an authority, boundary, or portability error. Fix what qualifies, within the scope the change already carries, and record what it was.

A finding does not qualify when it offers a rephrasing that changes no behavior, prefers a different degree of hedging, or says a sentence could be clearer without naming what breaks if it is not. Say so and leave the sentence alone. Neither the reviewer's confidence nor the length of its list is evidence.

Stop when a round returns only findings that do not qualify. Do not open another round to see whether it finds more, and do not re-review wording that survived a round unchanged. Improving instructions has no completion condition of its own; the observed defect is the completion condition.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance. Read prior decisions to understand earlier constraints and avoid repeating settled analysis. Reopen a decision when current host behavior, model evidence, product goals, security boundaries, or maintenance cost materially changes its premises. `docs/decisions.md` opens with the index of live decisions and their premises; the sections under it are history and rebuttable context, not a veto, and it links the immutable archive of the earlier ADRs and research.

Model behavior is proven only by deliberate receipts from real runs made with the host's own permission and budget controls. A receipt worth keeping holds everything fixed but the package: a throwaway fixture repository, a session carrying only the candidate package and the host's own built-ins, and the same prompt on both sides of the change. Isolate Codex by pointing both its own home and the operating system's home directory at a scratch location, because it also reads a host-agnostic user skill directory that its own home setting does not cover, and Claude by disabling every setting source and passing the package as a session plugin, which leaves authentication alone. Prove the isolation with a control run, and confirm it in the session transcript rather than by asking the model what it can see, before trusting anything built on it. Disabling the setting sources keeps the maintainer's own instruction files out of a session's context but does not stop the session from reading them with a shell command, so search each transcript for those files as well as for the package. Run the failing case before the change as well as after it, because a run that only shows the new behavior proves the wording is compatible with it, not that it produced it.

Keep a receipt small, because its cost is not proportional to what it settles: the 2.16.1 pass answered one yes-or-no question with forty sessions across fifty-one invocations, $165 and nearly five hours, and the four sessions that carried the answer cost under six dollars between them. Name the observable before running and stop each session once it lands rather than when the task finishes; where the observable is what a run does at the dispatch, paying for the delegates to finish buys nothing and costs most of the run, and where it is what they return, it does not. Read what earlier receipts recorded about the prompt shape that produces the behavior, pilot one session per arm, then run one more per arm and stop; a third is for when the two disagree. Keep one fixture, and when the pilot does not produce the behavior at all, fix the prompt from the record rather than by running another batch. Set a spending limit per session and a ceiling for the whole receipt, cap the sessions in flight, give every run its own fixture directory and log because two sharing one destroy each other's evidence, and read transcript write times before calling a run stuck, because a root blocked on a delegate looks the same as a hang.

Summarize claims and durable source links in `docs/evidence.md`; do not add one research file per run or release. A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

The behavioral corpus in `evals/` is arm-aware: every case states what must hold in every arm and what each arm may, must, and must not do, an arm with no package can never be required to produce a package-only event, and a case whose expectations no arm could satisfy is a defect the corpus tests catch. A paid run happens only on the owner's authorization under the limits recorded in the corpus, never from CI, and a passing corpus test moves nothing toward `Observed`.

## Writing instructions for the model

The shipped text and every delegate brief follow one prompt standard. State the goal, the context that settles it, the authority granted, the constraints, what success looks like, and what to report, in that order and in plain declarative sentences. Put the durable material first and the request last in a long prompt. Prefer a positive instruction to a prohibition and give the reason where one exists; use an example only where the shape is otherwise ambiguous; do not list steps where a capable model would infer them; name the observable rather than the process. Ask the model to reason only where the task warrants it, and route model and effort by the task's consequence and complexity rather than by a fixed tier. A sentence should carry an outcome, boundary, or useful method; remove redundant wording while retaining that responsibility's execution path. Do not assert how models in general behave without a source that shows it.

## Checks

Install the pinned dependencies with `python -m pip install -r requirements-dev.txt`; the checks install nothing and stop on an interpreter that misses a pin. Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. Before completion, run `python scripts/check.py` and `git diff --check`. For packaging changes, also run `python scripts/check_hosts.py`, which reports each host capability on its own row, and report an unavailable host as `UNVERIFIED`. `scripts/check.py` validates the single owner skill, its reachable modules and resources, the safety shape of any shipped hook, aligned versions, and portability boundaries such as personal paths and versioned model IDs. Change the check and `docs/decisions.md` together when those invariants change.

Every deterministic assertion belongs to one class: a package or host contract, a security or release invariant, or the semantic validity of the behavioral corpus, all of which fail the run; or an editorial or layout preference, which is at most a non-blocking lint; or an assumption about the current shape, which is deleted unless it is promoted into a stated contract with a reason. Do not pin a marketing sentence, a method roster or count, a role set, a hook matcher topology, a site presentation detail, or a prose budget with no measured limit behind it.

## Versioning and releases

Follow Semantic Versioning 2.0.0. The public surface is the runtime contract, not the file layout: owner-visible behavior, authority boundaries, default side effects, the public skill name and description, and any format a project keeps.

Use `PATCH` for repository, documentation, or wording changes that keep the promised behavior. Use `MINOR` for a capability, module, or behavior a project opts into, compatible with projects already installed. Use `MAJOR` for a change to the owner interface, an authority boundary, or a default side effect with no safe path for those projects.

Decide the number after the change is complete and its compatibility is known. Do not reserve a major version while planning.

Release one coherent, verified change set at a time. Bump `VERSION` and both manifests once, at the start of the branch that will carry the release, and keep that number through the branch; related work accumulates there rather than as a sequence of releases on `main`. Never edit or re-tag a released version. Claim a material change in model behavior only after receipts.

Every release publishes the compact validation matrix, one row per capability: the deterministic package gate, Codex and Claude schema validation, clean install on each host, explicit invocation, implicit activation, continuity, and the behavioral suite, each `PASS`, `FAIL`, `UNVERIFIED`, or `Observed`, with the behavioral row pointing at `docs/evidence.md` and never implied by CI. A skipped check stays visible as `UNVERIFIED`; it never disappears into a green aggregate.

## Portability and safety

Do not add personal paths, home-directory assumptions, credentials, telemetry, or network calls to the package or its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
