# Delivery

Use this reference for `DELIVER`. Carry the authorized outcome through implementation and fresh verification.

## Ground the work

Read repository instructions, inspect the relevant implementation, and preserve unrelated changes. Resolve routine reversible details from project evidence. Ask only when a missing product choice changes scope, cost, risk, or the public result.

Use the current session for a bounded task. Read [long work](long-work.md) for a selected queue, an external wait, unattended work, or recovery. Read [GitHub delivery](github.md) when the repository uses tracked delivery.

## Run project code safely

Treat tests, package scripts, build hooks, and changed executables as repository-controlled code. Inspect an unfamiliar entry point before running it. Use the host sandbox with the narrowest practical file, network, and process access. Remove unrelated credentials from the command environment and keep credentialed GitHub control outside worker code execution. Never accept an unsandboxed fallback merely to obtain a green check.

If the host cannot enforce a boundary required by the risk, do not pretend the check passed. Use a safer check or mark the affected claim `UNVERIFIED`.

## Prefer maintained code

Before creating a framework, scheduler, storage layer, authentication layer, protocol, or lasting abstraction, inspect current platform support, maintained dependencies, and suitable services. Compare fit, license, security, maintenance, operating constraints, and migration cost. Reuse a sound existing solution when adaptation costs less than owning new code.

Read [engineering methods](engineering.md) when a stable test seam, module boundary, prototype, conflict, or independent review needs more care.

## Change and verify

Make the smallest coherent change that solves the whole request. Add or update evidence that could fail for the original defect or requirement. Prefer observable behavior over internal details. Run focused checks during development and the repository-required final checks before completion.

Inspect the final diff, security boundaries, public contracts, failure paths, and cleanup. Use independent review when repository policy, risk, a public contract, or weak verification warrants it.

After a second failure with the same cause or failure signature, stop unchanged retries. Add the smallest durable prevention within scope, such as a test, lint rule, deterministic check, script fix, or skill correction. If that prevention is outside authority, save one deduplicated decision-ready finding. Resume only after the premise changes and the smallest reproducer passes.

## Account for findings

- Fix a blocker, immediate safety risk, or inseparable defect in the current work.
- Save one record for each independent actionable defect after a duplicate search.
- Save a material unknown as `NEEDS_RESEARCH`.
- Mark an invalid or obsolete finding `DISMISSED` with evidence.

Do not implement or reprioritize an independent finding merely because delivery authority allowed its record.

## Finish

Recheck the original request against the final state. Report the result and fresh evidence. Name any persisted follow-up, missing check, or external blocker. Never call an unavailable or stale check passed.
