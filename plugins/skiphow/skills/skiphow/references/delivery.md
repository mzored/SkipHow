# Delivery

Use this reference for `DELIVER`. Carry the authorized outcome through implementation and fresh verification.

## Ground the work

Read repository instructions, inspect the relevant implementation, and preserve unrelated changes. Resolve routine reversible details from project evidence. Ask only when a missing product choice changes scope, cost, risk, or the public result.

Use the current session for a bounded task. Read [long work](long-work.md) for a selected queue, an external wait, unattended work, or recovery. Read [GitHub delivery](github.md) when the repository uses tracked delivery. A repository rule that requires an Issue-linked branch or pull request owns the delivery shape even for a small change; reconcile it before implementation.

## Run project code safely

Treat tests, package scripts, build hooks, and changed executables as repository-controlled code. Inspect an unfamiliar entry point before running it. Use the host sandbox with the narrowest practical file, network, and process access. Remove unrelated credentials from the command environment and keep credentialed GitHub control outside worker code execution. Never accept an unsandboxed fallback merely to obtain a green check.

If the host cannot enforce a boundary required by the risk, do not pretend the check passed. Use a safer check or mark the affected claim `UNVERIFIED`.

## Prefer maintained code

Before creating a framework, scheduler, storage layer, authentication layer, protocol, or lasting abstraction, inspect current platform support, maintained dependencies, and suitable services. Compare fit, license, security, maintenance, operating constraints, and migration cost. Reuse a sound existing solution when adaptation costs less than owning new code.

Read [engineering methods](engineering.md) when a stable test seam, module boundary, prototype, conflict, or independent review needs more care.

## Change and verify

Make the smallest coherent change that solves the whole request. Add or update evidence that could fail for the original defect or requirement. Prefer observable behavior over internal details. Run focused checks during development and the repository-required final checks before completion.

If touched files already contain unrelated changes, capture their pre-change identities and diff before editing. Attribute implementation, checks, review, and candidate claims to the delta from that baseline. Preserve the earlier changes. If required tracked delivery cannot isolate or prove the candidate safely, mark that delivery `UNVERIFIED` or `BLOCKED`; do not bypass the repository gate.

Inspect the final diff, security boundaries, public contracts, failure paths, and cleanup. A private or internal value becoming public changes the data boundary: reconcile the owning durable decision or contract, keep unaffected projections unchanged, and verify consent withdrawal or equivalent exclusion behavior. Use independent review when repository policy, risk, a public contract, or weak verification warrants it.

After a second failure with the same cause or failure signature, stop unchanged retries. Add the smallest durable prevention within scope, such as a test, lint rule, deterministic check, script fix, or skill correction. If that prevention is outside authority, save one deduplicated decision-ready finding. Resume only after the premise changes and the smallest reproducer passes.

## Account for findings

Keep a lightweight working triage, not a second task database. Classify every credible candidate as `IN_SCOPE`, `PERSIST`, `DUPLICATE`, `EXPECTED`, or `NONMATERIAL`.

- Fix an `IN_SCOPE` blocker, immediate safety risk, or inseparable defect in the current work.
- For `PERSIST`, save one record for each independent actionable defect after a duplicate search. Save a material unknown as `NEEDS_RESEARCH`.
- Link `DUPLICATE` to its canonical record. Treat expected negative-test output as `EXPECTED` only when the test contract proves it. Use `NONMATERIAL` only with evidence that no actionable product, safety, or delivery risk remains.
- Mark an invalid or obsolete persisted finding `DISMISSED` with evidence.

A warning on the changed surface can weaken completion evidence even when the command exits successfully. Triage it before making a green claim. Do not persist benign expected output merely to prove it was seen.

Do not implement or reprioritize an independent finding merely because delivery authority allowed its record.

## Finish

Recheck the original request against the final state. Report the result and fresh evidence. Name every persisted follow-up, or state that triage found none material. Name any missing check or external blocker. Never call an unavailable or stale check passed.
