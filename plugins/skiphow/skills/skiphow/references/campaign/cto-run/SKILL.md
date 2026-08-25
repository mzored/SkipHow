---
name: cto-run
description: Legacy semantic handoff for durable execution.
---

# Durable campaign handoff

This compatibility contract does not provide a runner. The technical controller selects durable work and invokes the installed `durable_execution` capability described in `../../host-capabilities.md`.

Pass the runner:

- the original outcome verbatim;
- granted authority and protected-action limits;
- the task graph, dependencies, scope, and exclusions;
- required evidence and repository gates;
- saved decisions, findings, state identities, and exact next action;
- product-level cost, time, parallelism, merge, persistence, and stop settings.

The executable runner owns transactions, revisions, attempts, leases, checkpoints, provider sessions, external waits, retries, circuit breaking, pause, resume, cancel, recovery, reconciliation, and cleanup. Do not reproduce these mechanics in a runbook or claim that Markdown state makes a process durable.

Defining a hard-stop condition does not stop the run. The runner must record and enforce it. If `durable_execution` is unavailable, bounded work may continue in-session, but background and recovery claims remain `UNVERIFIED`.

Use `../../trackers/github-task/SKILL.md` only for authorized tracked lifecycle operations. Git, GitHub, CI, and providers remain authoritative for their own state.
