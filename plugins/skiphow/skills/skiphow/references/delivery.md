# Delivery

Use this reference for `DELIVER`. Carry the authorized outcome through implementation and fresh verification.

## Ground the work

Read repository instructions, inspect the relevant implementation, and preserve unrelated changes. Resolve routine reversible details from project evidence. Ask only when a missing product choice changes scope, cost, risk, or the public result.

Use the current session for a bounded task. Read `long-work.md` when work spans several tracked items, must wait on external state, or must survive interruption. Read `github.md` when the repository policy or work item requires tracked delivery.

## Prefer maintained code

Before creating a framework, scheduler, storage layer, authentication layer, protocol, or long-lived abstraction, inspect current platform support, maintained dependencies, and suitable services. Compare fit, license, security, maintenance, operating constraints, and migration cost. Reuse a sound existing solution when adaptation costs less than owning new code.

Do not require broad research for a small local change. Do not replace clear project conventions without evidence that they fail the requested outcome.

## Change and verify

Make the smallest coherent change that solves the whole request. Add or update tests that can fail for the original problem. Run focused checks during development and the project-required final checks before completion.

Review the changed behavior, security boundaries, public contracts, failure paths, and cleanup. Use an independent reviewer only when risk or weak verification warrants it.

Classify material findings as follows:

- Fix a blocker, immediate safety risk, or inseparable defect in the current work.
- Save an independent actionable defect after checking the canonical tracker for duplicates.
- Save a material unknown as `NEEDS_RESEARCH`.
- Mark an invalid or obsolete finding `DISMISSED` with a reason.

Do not expand the current scope merely because you saved a finding.

## Finish

Recheck the original request against the final state. Report the result and fresh evidence. Name any persisted follow-up, missing check, or external blocker. Never call an unrun or unavailable check passed.
