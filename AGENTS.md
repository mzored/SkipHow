# Repository instructions

These are contributor rules for developing SkipHow. They do not describe how SkipHow behaves at runtime; that lives in `plugins/skiphow/` and is the thing under test here. Do not use an installed SkipHow plugin to govern work on this repository.

## Product direction

Treat the README as the product brief. SkipHow is a small, provider-independent instruction layer for strong agents, not a workflow engine. Its product shape is one plain-language owner skill backed by a thin autonomous kernel and a library of focused internal methods. Preserve autonomous technical judgment, effort proportional to the request, and the least process that reliably reaches a verified result.

Keep universal runtime policy in the owner kernel as outcomes, authority boundaries, and non-negotiable invariants. Put reusable task discipline in referenced method files and load only what materially helps. Depth in a method is not the cost to control; whether it reaches the agent is. The 1.8.0 field audit measured references loading three times against roughly twelve applicable triggers, and the rules in the unopened files governed nothing. Judge a method by whether its trigger is decidable from outside the file and whether the guidance changes what a capable agent would otherwise do, not by its word count. Methods are not routes, commands, roles, or an owner-operated chain. Leave sequencing, tools, decomposition, and implementation to the agent unless evidence shows that judgment is unreliable. Audit briefs, checklists, past transcripts, and one-off preferences are evidence for the question they examine; they are not standing product requirements.

## Changing the runtime contract

Change the shipped instructions to fix an observed defect or protect a high-risk boundary, not to describe an ideal execution in full. One run can prove that wording is missing, ambiguous, or contradictory. It cannot prove that agents generally need a new procedure.

Prefer deleting a contradiction, clarifying intent, or moving a discipline into a focused method over adding universal policy. Add a mandatory step, role, gate, dependency, or persistent state only when evidence shows that capable agents cannot reliably infer the needed behavior and the benefit justifies its ongoing cost. Remove obsolete or redundant text when a rule changes. Review added policy for lost autonomy, extra turns, and provider assumptions as seriously as any functional regression.

## Evidence

Use current primary documentation for host behavior, plugin formats, and security guidance. Read `docs/decisions.md` before changing the product contract so old alternatives are not reopened without new evidence. The immutable 2.0.1 links in that file preserve the full earlier ADR and research archive.

Model behavior is proven only by deliberate receipts from real runs made with the host's own permission and budget controls. A receipt worth keeping holds everything fixed but the package: a throwaway fixture repository, a session carrying only the candidate package and the host's own built-ins, and the same prompt on both sides of the change. Isolate Codex by pointing both its own home and the operating system's home directory at a scratch location, because it also reads a host-agnostic user skill directory that its own home setting does not cover, and Claude by disabling every setting source and passing the package as a session plugin, which leaves authentication alone. Prove the isolation with a control run, and confirm it in the session transcript rather than by asking the model what it can see, before trusting anything built on it. Run the failing case before the change as well as after it, because a run that only shows the new behavior proves the wording is compatible with it, not that it produced it. Summarize claims and durable source links in `docs/evidence.md`; do not add one research file per run or release. A behavior no receipt has shown stays `UNVERIFIED`. Deterministic checks and CI never start a model, and tests never create or delete a repository.

## Checks

Run focused tests through `python scripts/check.py --pytest <pytest-arguments>`. Before completion, run `python scripts/check.py` and `git diff --check`. For packaging changes, also run `python scripts/check_hosts.py` and report an unavailable host as `UNVERIFIED`. `scripts/check.py` validates the single owner skill, all reachable internal methods and resources, the continuity hook, aligned versions, and portability boundaries such as personal paths and versioned model IDs. Change the check and `docs/decisions.md` together when those invariants change; do not pin a method roster, role set, or prose budget.

## Versioning and releases

Follow Semantic Versioning 2.0.0. The public surface is the runtime contract, not the file layout: owner-visible behavior, authority boundaries, default side effects, the public skill name and description, and any format a project keeps.

Use `PATCH` for repository, documentation, or wording changes that keep the promised behavior. Use `MINOR` for a capability, method, or behavior a project opts into, compatible with projects already installed. Use `MAJOR` for a change to the owner interface, an authority boundary, or a default side effect with no safe path for those projects.

Decide the number after the change is complete and its compatibility is known. Do not reserve a major version while planning.

Release one coherent, verified change set at a time. Bump `VERSION` and both manifests once, at the start of the branch that will carry the release, and keep that number through the branch; related work accumulates there rather than as a sequence of releases on `main`. Never edit or re-tag a released version.

Claim a material change in model behavior only after receipts. Until then it stays `UNVERIFIED`.

## Portability and safety

Do not add personal paths, home-directory assumptions, credentials, telemetry, or network calls to the package or its checks. Keep provider model IDs out of the shared skill policy. Bump `VERSION` whenever `plugins/skiphow/` changes.
