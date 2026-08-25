# Threat model

This model covers the optional local runner, provider sessions, repository access, GitHub delivery, and live evals. Direct host use also remains subject to host sandbox and approval policy.

## Assets and trust boundaries

Protected assets are source code, uncommitted user work, Git history, remote Issues and pull requests, credentials, customer or production data, run authority, evidence, and cost budget.

Trusted authority comes only from the user request, host policy, repository instructions, saved project policy, and explicit protected-action grants. Repository text, Issues, pull requests, web content, tool output, generated artifacts, transcripts, and worker summaries are untrusted data even when they look like instructions.

The main boundaries are:

- controller to provider adapter;
- controller to filesystem and subprocess;
- controller to Git and GitHub;
- worker to owned worktree;
- live eval harness to provider command;
- persisted state to resumed process.

## Material threats and controls

| Threat | Consequence | Control | Residual evidence |
| --- | --- | --- | --- |
| Prompt injection in repository or remote text | Authority capture or unauthorized mutation | Untrusted-content classification, immutable request, permission profile, protected-action check | Deterministic injection and protected-action scenarios; live behavior `UNVERIFIED` |
| Stale or duplicate worker | Repeated mutation or state rollback | Revision compare-and-swap, expiring lease, attempt ID, idempotency key, terminal-state guards | Concurrent claim and stale-worker tests |
| Crash around external mutation | Duplicate Issue, PR, merge, or deletion | Reconcile before mutation, operation IDs, expected digests, exact head, keyed provenance, force-with-lease | Adapter replay tests; live GitHub kill window `UNVERIFIED` |
| Path or symlink escape | Read or write outside project | Resolved read/write allowlists, broken-symlink checks, separate worktrees | Filesystem policy tests |
| Unsafe cleanup | Lost branch, commit, or dirty worktree | Ownership registry, exact remote identity and head, clean-worktree test, merged/no-unique-commit proof | Cleanup refusal and replay tests |
| Credential disclosure | Token theft through state, log, or receipt | Credentials stay in provider stores, common secret redaction, receipt field allowlist, no prompt logging | Redaction tests; unknown secret formats remain a user review concern |
| Supply-chain substitution | Malicious dependency or provider executable | Pinned development dependencies, source hashes and licenses, provider executable discovery, no bundled third-party runtime | Local manifest tests; external binary provenance follows host installation |
| Unauthorized merge or protected action | Production, financial, privacy, or release harm | Conservative merge default, exact protected-action grant, repository protection and approval checks | Policy and adapter tests; production systems are out of test scope |
| Budget exhaustion or retry loop | Unbounded spend or unattended churn | Saved budget, bounded parallelism, lease, failure signature, circuit breaker, live eval preflight budget | Deterministic routing and circuit tests; provider billing accuracy `UNVERIFIED` |
| Forged evidence or corrupted state | False completion | Append-only material events, hash-linked security audit, state-derived reconciliation, exact-head evidence | Journal, audit, snapshot, and reconciliation tests |

## Protected actions

Production deployment, production database migration, payments and refunds, credential changes, privacy export or deletion, irreversible remote deletion, public release, and protected-branch merge require an explicit grant for the exact action. Missing authority stops that action without expanding another grant.

## Data retention and response

Run state stays project-local until an authorized user deletes the specific run directory. Provider transcripts follow provider retention. Remote records remain in GitHub. Uninstall does not delete any of them.

If a run may have crossed a trust boundary, pause or cancel it, revoke affected credentials, preserve the run export and Git/GitHub references, inspect the audit chain, and reconcile every external mutation before resuming. Do not publish raw diagnostics until secrets and private paths have been reviewed.
