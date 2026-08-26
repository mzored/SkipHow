# Engineering methods

Load this reference when tests, a design seam, a prototype, a Git conflict, or a review beyond the root's closing pass needs more care than an ordinary change. It guides choices; it adds no commands, checkpoints, or ceremony, and an ordinary change should not acquire a design exercise.

## Tests

Test through an interface a caller or user observes, so the test survives a refactor. Take expected values from a worked example, a specification, or a captured known-good result, never from the implementation. Use a real local dependency when practical; mock only a true external boundary and assert results, not call order. Inject time, randomness, and network at the boundary that varies. For a bug, prove the test fails for the original defect before the fix. If no stable seam exists, record the verification gap instead of adding a brittle private-method test.

## Review

The root sends every project change to an independent reviewer (the `reviewer` role when the host supports it); a fresh reviewer helps but does not replace tests. Security, a public contract, a large integration, weak evidence, or a repeated failure widens what that review must cover. When it widens and the other host is installed, that pass goes there rather than to a same-model delegate; read [model routing](model-routing.md) for how each host is asked. Review the exact candidate: name the base commit and the head or tree, and treat a new head, dirty files, or changed executable inputs as invalidating the evidence. Judge against the owner request first and repository standards second. Each material finding names its evidence, affected behavior, impact, and either the fix that resolved it in scope or the tag it carries into the report. After a fix, re-review the finding and plausible regressions; repeat the full review only when the fix changed architecture, product behavior, or a security or privacy boundary.

## Design

Add a module only when it hides sequencing, policy, invariants, or error handling from its callers; if deleting it would push no complexity into the callers, it is a wrapper. Add a seam only where behavior varies. One implementation does not justify an adapter. Choose the smallest design that keeps product behavior clear and tests stable.

## Prototypes

A prototype answers one named question that inspection cannot settle cheaply. Write down the question, the evidence to observe, and the limit; skip hardening; keep it isolated from the release candidate and away from secrets and production. End with adopt, reject, or unknown, and remove it before delivery. Code worth keeping is rewritten under the normal rules; the experiment never ships unchanged.

## Conflicts

When Git is already in a conflicted merge or rebase, recover both sides' intent from the merge base, history, and tests before editing. Conflict markers show overlapping text, not every semantic conflict, so also check renamed symbols, moved files, schemas, and tests outside the markers. Resolve the combined intent when the changes are compatible; otherwise follow the owner request and accepted decisions, never the newer, larger, or easiest side. Do not abort, reset, or discard an operation unless the request authorizes it. Stage only the resolved paths, run checks for both intents, and report anything that could not be preserved.
