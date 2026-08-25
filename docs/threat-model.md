# Threat model

This model covers the SkipHow skill running inside Codex or Claude Code, optional GitHub delivery, host-native subagents and worktrees, and opt-in live evaluation.

SkipHow is policy, not an enforcement process. The host sandbox, approval system, credentials, and repository protections are the security controls that enforce access.

## Assets and boundaries

Protected assets include source code, uncommitted work, Git history, Issues, pull requests, branches, credentials, customer and production data, granted authority, completion evidence, and provider spend.

The relevant boundaries are:

- owner and host instructions versus repository, tracker, web, and tool content;
- root agent versus subagent context;
- one worktree versus another;
- local files and Git state versus GitHub, CI, databases, and deployments;
- the packaged candidate versus live-evaluation fixtures and collectors.

A subagent is not a security boundary. A worktree separates files but does not isolate credentials, network access, shared databases, or remote services.

## Threats and controls

| Threat | Consequence | Control | Remaining limit |
| --- | --- | --- | --- |
| Prompt injection in project or remote content | Unauthorized action or changed scope | Treat content as data; only owner and host authority grant actions; repository rules can narrow authority | Policy text cannot replace the host sandbox |
| Scope expansion through dependency discovery | Unapproved work enters a campaign | Keep the selected queue fixed; dependencies change readiness only; route new findings through intake | A broad owner request may still need product clarification |
| Unauthorized mutation or protected action | Production, privacy, financial, or repository harm | Host approvals, least privilege, exact grants, protected-action stop | Host and connector behavior varies by version |
| Concurrent writers | Conflicts, duplicate pull requests, or overwritten work | One root integrator, disjoint worktrees, active-operation checks across Issues, pull requests, branches, and markers | Worktrees do not isolate shared external systems |
| Stale or duplicate GitHub mutation | Duplicate records or merge of an unchecked head | Treat markers as correlation only; bind repository, object, operation, branch, and head; reconcile before retry | GitHub create APIs do not promise exactly-once behavior |
| Unsafe cleanup | Lost branch, commit, or local work | Confirmed merge, operation ownership, clean worktree, no other pull request, no unique work, compare-and-delete expected identity | Uncertain resources stay in place for review |
| Credential disclosure | Secret exposure through prompts, files, or remote records | Keep credentials in host stores, limit access, do not persist secrets | A model with granted access may still see in-scope secrets |
| Forged completion evidence | False success or unsafe merge | Bind review to repository, base and candidate trees, clean state, executable inputs, configuration, required checks, and current remote state | Some outcomes need live or human checks |
| Retry or delegation loop | Unbounded cost and stalled work | Host budget, bounded retries, reconciliation after timeout, changed premise before retry, explicit blocker | Provider cost reports and hard limits differ |
| Malicious repository-controlled checks | Credential loss, destructive commands, or false evidence | Inspect unfamiliar tests and scripts before execution; run with least privilege and host isolation | Full behavior may depend on tools outside the repository |
| Checkpoint injection or disclosure | Stale authority replay, secret exposure, or unsafe recovery | Treat checkpoints as untrusted data; bound and redact fields; exclude credentials, private absolute paths, and instructions | Cross-process recovery is not proven on every host |
| Compromised live fixture or collector | False release claim or access to real data | Synthetic fixtures, collectors outside writable roots, recursive receipt redaction, repository-free package sources | Mutable GitHub behavior remains `UNVERIFIED` without an enforced repository-preservation boundary |

## Protected actions

Production deployment or migration, payments or refunds, credential changes, privacy export, deletion, or disclosure, public release, repository setting or protection changes, and irreversible remote deletion need an exact user grant.

Tracked end-to-end delivery may include merge and cleanup only for its selected scope. A ready frontier cannot expand that scope. Protected actions still require the exact candidate identity, accepted required checks and reviews, current remote state, and repository protections. SkipHow never uses an admin or bypass option.

## Data and incident response

SkipHow sends no telemetry and has no private state store. Data may remain in host sessions, provider transcripts, Git, GitHub, `.skiphow/inbox.md`, and `.skiphow/handoff.md` according to the system that owns it.

If work may have crossed a boundary, stop new actions, revoke affected credentials, preserve Git and GitHub references, inspect every external mutation, and resume only after authority and current state are clear. Do not publish diagnostics until private paths, customer data, and secrets have been removed.

The [trust guide](trust.md) explains these rules for users. The [2026-08-25 security audit](research/2026-08-25/security-and-evals.md) records why the previous custom runtime was removed. The [1.0 audit](research/2026-08-26/release-1.0-audit.md) records the campaign, authority, and packaging corrections.
