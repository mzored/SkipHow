# ADR 0006: Keep campaign and engineering policy host-native

## Status

Accepted. Amended by [ADR 0007](0007-host-adapters-for-routing-and-continuity.md): the checkpoint is written at item boundaries and before long waits rather than "before compaction", and a host hook surfaces it after compaction or resume.

## Date

2026-08-26

## Context

The 0.9 rewrite correctly removed SkipHow's Python runner, scheduler, task database, provider adapters, and copied host policy. The first migration was too narrow. It retained the idea of host-native long work but dropped parts of the product contract that made long campaigns recoverable and engineering work consistent.

Long work needs more than a sentence telling the host to use background tasks. It needs a stable selected queue, dependency-aware readiness, bounded delegation, health signals, checkpoints, recovery reconciliation, exact-candidate review, and a terminal accounting of every selected item. Engineering work also needs focused methods for testing, technical review, design, prototypes, and conflict resolution. Loading all of that policy for every request would make the owner-facing skill harder to inspect and more expensive to use.

The policy must not recreate the retired runtime. Fixed timeouts, a private event journal, a second task database, a SkipHow daemon, or a provider bridge would duplicate host and GitHub state. They would also create new recovery and security boundaries.

## Decision

SkipHow keeps one canonical owner-facing skill. The core file contains the owner contract, authority boundary, routes, and completion rule. It links to compact lazy policy references. Focused engineering methods live below an engineering router and load only when the task needs them.

Long work uses a host-native campaign protocol:

1. The owner request and host policy grant authority. Repository rules and accepted decisions may narrow it, but they cannot add actions or scope.
2. The root selects the campaign queue from the authorized outcome. It stays fixed unless the owner granted a bounded dynamic eligibility rule. Dependency state changes the ready frontier, not the selected scope.
3. The root assigns bounded worker packets with explicit inputs, outputs, ownership, authority, evidence, and stop conditions. Workers receive the least authority needed. The root keeps credentials, integration, external mutations, protected actions, and cleanup.
4. Campaign health uses both progress and operating signals. A diagnostic limit triggers reconciliation, reduced concurrency, or a blocked report. It does not silently cancel authorized work.
5. The root writes a bounded checkpoint before a long wait, costly operation, compaction, or handoff. The checkpoint records facts needed for recovery and excludes credentials, private absolute paths, and untrusted instructions.
6. Recovery re-reads the owner request and host policy, then reconciles Git, GitHub, workers, and recorded external actions. A timeout does not justify a retry before reconciliation.
7. Review binds the exact repository, base and candidate trees, clean state, untracked executable inputs, submodules, configuration, checks, and remote state that affect the result.
8. Completion reconciles every selected item and records each as delivered, blocked, deferred by the owner, or otherwise explicitly disposed. The same failure cause twice requires a systemic prevention step or a documented reason it is not practical.

SkipHow expresses diagnosis, testing, review, design, prototyping, and conflict resolution as compact policy. It does not ship a method runner or require every method on every task.

## Consequences

Long work has a recoverable contract without a SkipHow process that must stay alive. Owners can inspect tracked state in the host, Git, and GitHub. Routine work still loads a small core skill.

Behavior depends on host capabilities. If a host cannot preserve tasks, isolate mutable work, wait independently, or resume after restart, SkipHow completes a safe bounded portion and reports the missing guarantee as `UNVERIFIED`.

The root has more integration responsibility. That concentration is deliberate because external writes and credentials cannot be isolated by a subagent prompt or a worktree.

## Rejected alternatives

### Restore the Python runner

This would restore duplicate scheduling, state, provider, and recovery systems without proving better owner outcomes.

### Split methods into several public skills

This would make owners choose an engineering workflow and would duplicate routing policy across host packages.

### Load every method for every request

Most requests need only the core contract and one focused reference. Eager loading would add unrelated instructions and make policy review harder.

### Use fixed universal timeouts and worker counts

Hosts and tasks differ. Health values are diagnostics chosen from current host and task evidence, not portable product constants.

### Let dependency discovery expand the queue

Readiness and authorization answer different questions. New work needs owner authority or the normal finding and intake path.

## Evidence

- [Release 1.0 audit](../research/2026-08-26/release-1.0-audit.md)
- [OpenAI Codex skills](https://developers.openai.com/codex/skills.md)
- [OpenAI Codex plugins](https://developers.openai.com/codex/plugins.md)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins.md)
- [Prior-art research](../research/2026-08-25/prior-art.md)

## Revalidation triggers

Revisit this decision when a supported host removes progressive skill loading or task recovery, host-native campaigns repeatedly lose selected work, fixed policy cannot describe a required compliance control, or measured route size makes the lazy reference layout ineffective.
