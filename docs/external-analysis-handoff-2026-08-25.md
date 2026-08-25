# External analysis handoff — 2026-08-25

This document marks the exact stopping point of the SkipHow refactor. It is
intended for an independent reviewer and is not a release-completion claim.

## Scope completed in the working tree

The refactor now contains the lean plugin kernel, Product Intake pipeline,
optional SQLite runner, schema migrations and recovery, provider adapters,
durable semantic routing, runtime security and audit records, environment
verification, context compaction, GitHub delivery reconciliation, host package
checks, the twenty-scenario eval registry, and an opt-in live-eval harness.

The last fully published candidate before this handoff was
`fd906228a6d5370ece94c286af453df0b79043e7`. Its GitHub pull-request CI passed
on Python 3.11 through 3.14. Exact-candidate host packaging and a disposable
GitHub Issue-to-merge crash/resume gate were also verified for that commit.
Those receipts do not cover the later changes in this handoff.

## Where work stopped

Work was paused during a second independent-review remediation pass. Several
agents were interrupted after editing the shared working tree, so the final
archive must be reviewed as an analysis snapshot rather than a release.

The last complete repository test run before that interrupted pass reported
`325 passed`. A later run after part of the pass reported `327 passed`, but the
remaining interrupted edits had not received a final exact-tree review, host
package receipt, GitHub lifecycle receipt, or live-provider receipt when work
was paused.

The interrupted work covered:

- stronger materialized-state and audit verification in the SQLite store;
- race-safe snapshot restoration and v1 snapshot migration;
- sandboxing verifier commands and covering verifier time in run deadlines;
- pending-lease renewal for serialized writable claims;
- atomic task completion and route-outcome evidence;
- cancellation handling that does not consume retry budget;
- typed protected-action enforcement beyond text inference;
- runtime CLI persistence to GitHub Intake;
- relationship-error classification and Git ref validation;
- process-group termination for timed-out live provider adapters; and
- expansion of independent live collectors beyond the initial supported rules.

Some of those edits may already be present. Reproduce each finding against the
archived tree before changing it; do not assume either the old finding or a
partial fix is still current.

## Material release gaps

SkipHow 1.0 has not been declared. At pause time:

- Claude was installed but not authenticated for a live run.
- No explicit live-eval spending limit had been supplied.
- Multi-provider, multi-trial release outcomes had not been run.
- Adaptive-vs-balanced-vs-frontier routing ablation had not been run.
- The live fixture layer was being expanded from partial independent collector
  coverage; unsupported rules correctly remained `UNVERIFIED` rather than
  trusting model-reported observations.
- Cross-platform runtime evidence remained incomplete.
- Exact host and GitHub receipts needed regeneration for the final merged SHA.

The `gh` CLI resolved the GitHub credential question only. It does not provide
Claude/OpenAI provider credentials, a live-eval budget, or behavioral evidence.

## Recommended review order

1. Run `git diff --check` and `python scripts/check.py --pytest -q`.
2. Reproduce the interrupted-review items above against the exact archive.
3. Review store migrations, restoration, and audit integrity before trusting
   persisted completion state.
4. Review verifier isolation, protected actions, leases, cancellation, and
   atomic route evidence before running unattended campaigns.
5. Review GitHub Intake and delivery idempotency at external mutation windows.
6. Confirm that every live rule is derived from hidden, immutable evidence and
   that adapter timeouts kill all descendant processes.
7. Only after fixes, regenerate exact-head deterministic, host, GitHub, and
   budgeted multi-provider receipts.

## Files outside version control

At handoff time the workspace also contained `refactor-spec.md` and
`sqlite-desicion.md`. They were preserved as supplied source material and were
not treated as product code. The external archive includes them separately,
along with the original `SKIPHOW_FINAL_REFACTOR_SPEC_RU.md` from Downloads.
