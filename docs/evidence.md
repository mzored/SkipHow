# Current evidence

This page separates package checks from observed model behavior. The full 2.0 evidence remains in the immutable [`v2.0.1` research snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research/2026-08-27).

## Deterministic package evidence

`python scripts/check.py` verifies:

- one public owner skill;
- reachable internal Markdown references;
- valid JSON, YAML, Markdown links, manifests, and marketplace catalogs;
- aligned package versions and required release metadata;
- the continuity hook shape;
- third-party source attribution;
- package portability boundaries for personal paths and versioned model IDs.

`python scripts/check_hosts.py` runs available Codex and Claude package validators. It also attempts isolated installation in fresh host homes and compares every installed regular file with the candidate package.

These checks do not start a model and do not prove runtime behavior.

## Observed behavior

Six one-off Codex runs exercised the 2.0 owner-skill tree recorded in the [full receipt](https://github.com/mzored/SkipHow/blob/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research/2026-08-27/v2.0-codex-receipts.md). The fixtures exposed exactly one project skill and did not name SkipHow in their prompts.

The runs observed:

- one small change completed with tests and a clean commit;
- diagnosis and product-choice requests stayed read-only;
- broad autonomy plus a repository procedure did not grant protected actions;
- an explicit local protected-action fixture was accepted without claiming an external effect;
- one visual interaction reached a tested clean commit.

These are observations, not a general reliability rate. User-level skills were present and remain confounders.

## Still unverified

The retained receipts do not prove:

- a general implicit-selection rate;
- Claude model behavior;
- continuity across compaction or restart;
- real production or public-delivery actions;
- comparative cost or speed;
- behavior in the owner's real application.

SkipHow 2.3.0 adds decomposition as its own method and gives it a trigger a run can evaluate before starting: more than one independently verifiable outcome. Delegate briefs now carry a completion condition and a boundary, a delegate returns a blocking unknown as a question, every accepted unit must reach a named end, the tracker is read as well as written, and a batch of observations is grouped by cause before it becomes records. Deterministic checks cover the package. No receipt covers any of it, so it stays `UNVERIFIED`: whether large work is actually split into independently verifiable units, whether concurrent lanes still reconcile completely, whether one cause stops becoming several records, and whether small work still completes without added ceremony.

SkipHow 2.2.0 restores execution discipline the 2.0 cut removed: a reuse-first order before building something custom, budgets and anomaly response for long or stalled work, a stop after three failed attempts against one hypothesis, regression tests that close a bug class, staged verification, independent confirmation of risky results, and a concrete statement of what does not count as evidence. Deterministic checks cover the package. None of it is verified by receipt yet, including whether the added depth changes any outcome, so all of it stays `UNVERIFIED`.

SkipHow 2.1.0 changes the runtime contract. A project change now also grants the durable records the project keeps for that work, a one-time owner question settles where those records live, and three methods join the library for project setup, technical design, and delegation. Deterministic checks cover the package. No receipt yet covers the new behavior, so all of it is `UNVERIFIED`: whether a finding is recorded once and picked up by a fresh session, whether an interrupted run resumes from the record, whether a read-only request still writes nothing, and whether small work still completes without added ceremony.
