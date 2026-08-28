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

SkipHow 2.0.2 changes repository documentation, maintenance files, and package version metadata. The runtime owner skill, internal methods, and hook text remain unchanged from 2.0.1, so no new behavior claim is added for this release.
