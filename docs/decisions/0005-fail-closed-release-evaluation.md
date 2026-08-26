# ADR 0005: Keep release evaluation repository-free and fail closed

## Status

Superseded by [ADR 0008](0008-receipts-over-a-live-harness.md) for the evaluation mechanism. The claims policy (deterministic checks prove the package, missing evidence is `UNVERIFIED`) stands.

## Date

2026-08-25

## Context

SkipHow needs release evidence without restoring a product runner or giving a grader authority over the candidate. Package and live checks must not create or delete a repository. Receipts must not retain provider credentials, private local paths, or raw structured fixture values.

Codex can install a plugin from a local marketplace or a Git source. A Git source may be cloned inside host-managed cache state, so a temporary remote-source install violates the repository-lifecycle boundary even when the check itself never invokes `git clone`. Claude can validate a package and load it directly with `--plugin-dir` in bare mode. Its sandbox can restrict filesystem and network access, but a mutable GitHub delivery trial still needs write access to Git metadata. The current harness cannot allow those writes while technically preventing deletion of the same repository.

An operator-controlled routing map can compare the cost of recorded routes. It cannot prove that the installed skill selected those routes autonomously.

## Decision

Deterministic checks remain local and never start a model. Host package checks use repository-free local marketplace snapshots, reject links and special files, and compare the installed package bytes with the candidate. A managed policy that blocks the safe installation path is `UNVERIFIED` unless the release explicitly requires that host install.

Live Codex trials accept only a pre-provisioned plain local marketplace whose manifest and plugin bytes match the committed candidate. Remote Git marketplace sources are rejected. Live Claude trials validate and load the exact candidate with `--plugin-dir`, bare mode, a fresh config, required sandbox startup, and unsandboxed command fallback disabled.

Receipt serialization recursively redacts known credentials and private run paths. Structured collectors retain comparison results, counts, hashes, and mismatches, not raw JSON values, inbox records, GitHub snapshots, or workspace paths.

Codex live evaluation may use the current ChatGPT OAuth profile when the operator forbids API-key spending. This mode never copies the OAuth credential. It removes ambient API keys, ignores user config, uses ephemeral sessions, verifies the enabled cached plugin payload byte for byte, and requires an exact host-invocation cap. Because auth and plugin state still come from the existing profile, profile isolation remains `UNVERIFIED`.

The mutable GitHub scenario fails closed before credentials or host execution. It remains `UNVERIFIED` until an external boundary can preserve repository existence while permitting only the required Git and GitHub operations. A confirmation flag is not such a boundary.

Routing receipts report cost ablation under the operator-controlled map separately from autonomous route selection. The latter stays `UNVERIFIED` until host telemetry demonstrates it.

## Consequences

The evaluator remains release tooling, not a second runtime. Safe local and package evidence can run independently of paid GitHub delivery. The project cannot cite this harness as proof of unattended GitHub delivery, repository cleanup, autonomous model selection, or routing savings.

Codex installation may be `UNVERIFIED` under a managed policy that accepts only Git sources. This is preferable to turning a forbidden repository clone into a passing release check.

## Rejected alternatives

### Install Codex from an exact remote ref

Commit identity does not prevent the host from materializing and deleting a repository in its cache. Version and enabled status also do not prove package-byte identity.

### Trust a mutable GitHub sandbox confirmation

User confirmation grants authority; it does not enforce repository preservation against a model or subprocess.

### Remove the GitHub outcome contract

The versioned fixture and collectors still define the missing evidence. Keeping them fail closed makes the limit visible and provides a target for a future external boundary.

## Evidence

- [Release-readiness audit](../research/2026-08-25/release-readiness-audit.md)
- Evaluation policy (formerly `docs/evals.md`, removed with the harness in 1.1.0; see [ADR 0008](0008-receipts-over-a-live-harness.md))
- [Codex plugin documentation](https://developers.openai.com/codex/plugins.md)
- [Claude Code plugin documentation](https://code.claude.com/docs/en/plugins)
- [Claude Code sandbox documentation](https://code.claude.com/docs/en/sandboxing)

## Revalidation triggers

Revisit this decision when a supported host exposes a repository-preserving Git boundary, a direct exact-package load for Codex, installed-payload attestations, or trustworthy autonomous route telemetry.
