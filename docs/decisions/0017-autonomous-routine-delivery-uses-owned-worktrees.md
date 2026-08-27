# ADR 0017: Autonomous routine delivery uses owned worktrees and exact aggregate evidence

## Status

Accepted. Supersedes the phrase-based routine merge boundary in [ADR 0004](0004-github-lifecycle-and-authority.md) and [ADR 0015](0015-unconditional-invariants-live-in-the-root.md). Amends [ADR 0009](0009-reviewer-inherits-and-one-engineering-reference.md) on exact aggregate review and [ADR 0016](0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) on re-sizing after owner turns.

## Date

2026-08-27

## Context

SkipHow 1.13 treated one phrase and its equivalents as a merge capability. That made workflow wording the boundary instead of the owner's requested outcome. It also allowed a technically finished unit to stop before routine integration unless the owner knew the phrase.

A completed external session exposed the larger failure. It began as one bounded UI change, then six independent or systemic additions arrived in later owner turns. The run did not re-size, read repository instructions, load the long-work or GitHub lifecycle, or use the other installed host for widened review. Another session changed the shared checkout while it worked. The run lost and recovered changes, created a temporary empty commit, then made the final commit with an alternate index, `commit-tree`, and a direct ref update. The final commit existed, but hooks and exact-candidate evidence no longer described the path that produced it.

Worktrees are the established isolation mechanism. Git gives each linked worktree its own working files while sharing repository history. Claude Code provides native worktree isolation on named branches and blocks writes back into the main checkout. Codex delegates share the session sandbox, and Codex-managed worktrees may start detached, so the root must create or anchor the worktree and bind every builder call to it. Isolation alone does not always provide a durable branch ref.

The requested product boundary is semantic: the agent autonomously performs technical delivery through the non-production integration branch. The owner is asked only for an unresolved material product choice or at promotion into staging or production. Protected actions outside ordinary delivery still require their exact grant.

## Decision

- Infer authority from the requested outcome, never from a required phrase. An outcome that needs a project change grants its routine technical delivery. Explicit prohibitions narrow the grant immediately.
- Infer the routine integration target from repository instructions, deployment and release configuration, live branch protections, and recent merged pull requests. Require affirmative evidence that it is non-production; never hardcode `dev`, `main`, or the default branch. Ambiguity is a rollout decision, not routine merge authority. Branch from the target's exact live head.
- Ask at the point of promotion into a repository-declared staging or production branch, including `main` when it is production. Bind approval to source head, target head, and resulting tree; identity changes require renewed approval. Do not ask for worktrees, branches, ordinary commits, required Issues and pull requests, review loops, conflict resolution, routine integration, Issue closure, or safe owned cleanup.
- Re-read repository instructions, Git identity, and observable active host tasks before mutation. When no task inventory exists, assume other writers are possible and use fresh exclusive isolation. Re-size after every owner turn. Independently landable additions become explicit queue units.
- One writing lane owns one worktree and one named branch. A detached lane gets an owned ref before a deliverable commit or before cleanup. A Codex builder receives an already-created worktree and must bind every tool call to it.
- On checkout, branch, `HEAD`, status, or active-task drift, stop writes. Never commit in the uncertain checkout. Move only a proven owned tracked delta and owned untracked files to fresh isolation. Never use alternate indexes, plumbing commits, direct ref movement, force checkout, hook bypass, or forced worktree add/removal to manufacture completion.
- Every builder commits its owned delta through the repository's ordinary commit path and hooks. The root verifies and integrates every returned commit; a unit is not done before integration.
- Bind checks and review to target head, source head, and resulting committed tree after hooks. After all units are integrated and the target is current, run fresh affected checks and independent review on the exact aggregate candidate. Target movement, integration, hook changes, conflict resolution, or later edits invalidate applicable evidence. Fixes are re-reviewed.
- Resolve only a merge or rebase operation recorded as owned. Recover both intents from the base, commits, Issue, pull request, accepted decisions, and tests. Preserve both when compatible; ask only when incompatibility is a material product choice.
- Clean up only after confirmed merge and durable evidence proves no source content is absent from the result. Host-managed or current worktrees use safe exit or handoff before the final response when context survives; otherwise the host owns later cleanup and the run reports it pending. Git removal is only for operation-created, non-current clean worktrees. Squash or rebase cleanup requires the PR's source and resulting target plus content equivalence; otherwise leave and report every source ref.

## Consequences

Owners no longer need workflow vocabulary. Routine work reaches the integration branch without intermediate questions, while staging and production retain a deliberate product gate. Parallelism costs more setup and aggregate review, but each result has a branch, base, commit, and merge path that can be inspected.

The package gains `references/worktrees.md`. The root grows to carry rules that must survive missed reference loads. Independent review added fail-closed target inference, unavailable-task handling, host-owned cleanup, and exact aggregate evidence, so the accepted limit is 1,400 words and 9,500 bytes. Nine references may total 5,200 words, with 750 per file. These remain drift bounds, not compression targets.

Deterministic checks can prove package structure, forbidden phrase absence, continuity anchors, and release ancestry. They cannot prove that a model obeys the new workflow. Every runtime claim remains `UNVERIFIED` until an installed 1.14 session supplies a receipt.

## Rejected alternatives

### Keep a magic phrase as the merge grant

It makes owners learn implementation vocabulary and lets a semantically clear request stop before its result. The owner asked for the agent to choose and adapt its own workflow.

### Ask before creating a worktree

Isolation is a reversible engineering mechanism inside delivery authority. Asking adds the interruption this decision removes and does not improve product control.

### Work in place until a collision is observed

Detection comes after attribution is uncertain and data may already be lost. Parallel or ambiguous ownership starts isolated.

### Review each unit but not the aggregate

Clean integration can still create semantic interactions, and target movement changes the merge result. Only aggregate evidence covers what will enter the target branch.

### Always abort or never abort a conflict

Either command can destroy intent when applied mechanically. Ownership and recoverable intent decide whether to complete or restart; a foreign operation is never touched.

### Enforce the process with destructive Git hooks

Hooks are repository-controlled code, vary across hosts, and can be bypassed or affect unrelated users. The package keeps policy portable and proves the final candidate instead.

## Evidence

- [Field audit, 2026-08-27](../research/2026-08-27/field-audit-2026-08-27.md)
- [Git worktree documentation](https://git-scm.com/docs/git-worktree)
- [Claude Code worktree documentation](https://code.claude.com/docs/en/worktrees)
- [Superpowers worktree skill](https://github.com/obra/superpowers/blob/main/skills/using-git-worktrees/SKILL.md)
- [Resolving merge conflicts skill](https://github.com/mattpocock/skills/blob/main/skills/engineering/resolving-merge-conflicts/SKILL.md)
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets), [pull request reviews](https://docs.github.com/en/pull-requests/reference/pull-request-reviews), and [merge queues](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue)

## Revalidation triggers

Revisit when a receipt shows a 1.14 or later run asking for routine delivery mechanics, writing outside its owned worktree, losing a later owner item, committing through a bypass path, skipping aggregate review, merging against a changed target without renewed evidence, or promoting into staging or production without approval. Revisit the host procedure when Codex or Claude Code supplies stronger native isolation or changes detached-worktree behavior.
