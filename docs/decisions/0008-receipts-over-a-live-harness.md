# ADR 0008: Prove model behavior with receipts, not a live harness

## Status

Accepted. Supersedes [ADR 0005](0005-fail-closed-release-evaluation.md) on the evaluation mechanism; its claims policy stands. On 2026-08-26 the host's `claude plugin eval` (with a no-plugin baseline arm) existed but was early access and unavailable to this project; [ADR 0009](0009-reviewer-inherits-and-one-engineering-reference.md) records that it is the intended path once available.

## Date

2026-08-26

## Context

ADR 0005 introduced an opt-in live evaluator (`evals/live`, about 1,400 lines plus 700 lines of tests, fourteen scenarios with fixtures, oracles, and collectors). Across releases 0.9, 1.0, 1.0.1, and the 1.1 work it produced no receipt. The scenario that matters most to the owner, multi-Issue GitHub delivery, failed closed by design because the harness could not both allow Git writes and technically prevent repository deletion. Every release therefore shipped with the same `UNVERIFIED` line for live behavior, and the harness cost maintenance on every policy change.

The [system review](../research/2026-08-26/system-review.md) concluded that one real run of the owner's daily flow, written up honestly, says more than the harness can.

## Decision

The live harness is removed. Model behavior is proven by receipts: a real run of a scenario on a real or throwaway repository, recorded under `docs/research/<date>/` with what was asked, what happened (Issues, pull requests, delegations and their effective models, host cost when reported), what was cleaned up, and what went wrong.

A field-audit report may have an adjacent `field-audit-<date>.receipts.json` sidecar. That file is not a
model-evaluation schema and does not replace the narrative receipt. It stores only the transcript identity,
root record count, observed plugin-version values, and evidence fingerprint needed to tell whether the
private transcript evidence has changed since the report was written. Coverage reads this strict sidecar,
not Markdown presentation. A missing, malformed, incomplete, or stale key proves no coverage.

The claims policy from ADR 0005 stands: deterministic checks prove only the named package invariants they
inspect; host validators prove only their static validation result; and a successful isolated-install check
proves only that the exact candidate files were installed in that isolated local setup. Anything no receipt
has shown is `UNVERIFIED`. README and changelog copy may not claim behavior without a receipt.

Deterministic checks and CI never start a model. Receipts are produced by a person or an agent on purpose, with the host's own permission mode and budget flags.

## Consequences

About 3,500 lines of harness, fixtures, oracles, and tests leave the repository. Release evidence remains a
short document rather than a behavioral JSON result schema. A small field-census sidecar can establish only
that the document was written against the same mechanically observed transcript evidence. Coverage is
narrower and more honest: a behavioral receipt exists for a scenario or it does not, and freshness is
separate from the quality of its ruling.

## Rejected alternatives

Keep the harness and cut it to three scenarios: still no path to the GitHub scenario, still a schema to maintain. Replace it with `claude plugin eval` or a similar host feature: worth revisiting when a host feature can drive the owner's flow end to end on both hosts.

## Revalidation triggers

Revisit when a host ships an evaluation feature that can run the daily flow with GitHub on a sandbox repository, or when receipts show a regression the deterministic checks could have caught.
