# Parallel orchestration proposals

## Record

- Reviewed on 2026-08-26.
- Method: the bodies of issues 787 and 885 in `mattpocock/skills` and that repository's current skill list were fetched and read. Nothing was cloned, so these are issue-level and README-level findings.
- Purpose: the [prior-art mechanics](prior-art-mechanics.md) note surveyed that repository's shipped skills and took borrow 7 from them. It did not cover the two orchestration proposals sitting in its issue tracker, and a later suggestion to adopt them reached the owner. This note records what they propose and how each mechanic maps onto the shipped contract, so the next release does not read them again.

## What the proposals are

Both are open contributor proposals with no maintainer response. The official skill set still has no parallel orchestrator: `wayfinder` plans an effort larger than one session and resolves its decision tickets in order, one session at a time.

Issue 787 proposes a `swarm` skill that implements a parent issue's child tickets in parallel. It validates that the argument is a parent ticket, creates a `task/<slug>` integration branch, asks the owner once for run mode, subagent model, and effort, then computes the frontier of tickets with no open blockers and dispatches one subagent per ticket into its own git worktree on an `issue/NN` branch. Each worker implements, runs the project checks, calls the review skill, and commits. The orchestrator merges finished branches into the integration branch one at a time, keeps it green, and recomputes the frontier after each merge. A worker that meets an unsettled product question posts it as an issue comment with a `needs-info` label instead of guessing, and its ticket is parked while the rest continue. The owner sees only state transitions, never worker transcripts. The final merge to the default branch is left to a human. The skill also notes that subagents cannot invoke `/implement`, because that skill sets `disable-model-invocation: true`, so the dispatch prompt carries the implementation workflow inline.

Issue 885 proposes `docs/agents/orchestration.md`, written by the setup skill, declaring three environment facts: whether a human is at the terminal, the command to run when work finishes and whether it closes the work item, and the command that handles a blocking question. It names three gaps that stop those skills from running headless. `/implement` "ends at the commit and never touches the work item", so a dependency graph stalls because blockers never close. Blocking questions "have no escape hatch when no human is attached". And "the blocking graph it publishes has no machine-readable form".

## Mapped against SkipHow

| Mechanic in 787 | Where SkipHow already has it |
| --- | --- |
| Parent issue decomposed into child tickets | [long work](../../../plugins/skiphow/skills/skiphow/references/long-work.md): an epic is decomposed into bounded Issues, sub-issues when the tracker supports them, and that set is the queue |
| Frontier of tickets with no open blockers | Same file: dependencies decide readiness, and they never add scope |
| One subagent per ticket in its own worktree | Same file, plus the `builder` adapter, which carries `isolation: worktree` and no remote writes |
| Sequential merge that keeps the branch green, frontier recomputed after each | [GitHub delivery](../../../plugins/skiphow/skills/skiphow/references/github.md): the root serializes every GitHub mutation, re-reads live state before any merge, and closes the Issue and anything that depended on it |
| Owner sees state transitions, not transcripts | [model routing](../../../plugins/skiphow/skills/skiphow/references/model-routing.md): a delegate returns a summary, never a transcript |
| Park a blocking question and keep the rest running | [long work](../../../plugins/skiphow/skills/skiphow/references/long-work.md): four reasons justify stopping to ask, anything else is a recorded ruling, and a repeated failure becomes `BLOCKED` with the exact next action while the queue continues |
| Reviewer checks the spec and the standards | The `reviewer` adapter judges the candidate against the owner request first and repository standards second |
| Ask the owner once for run mode, model, and effort | Rejected in [ADR 0006](../../decisions/0006-host-native-campaign-and-engineering-policy.md): fixed universal timeouts and worker counts are diagnostics chosen from current host and task evidence, not portable product constants |
| Orchestrator may add a missing blocking edge | Rejected in the same ADR: readiness and authorization answer different questions, and new work needs owner authority or the normal intake path |
| Dispatch prompt carries the workflow inline, because a subagent cannot call `/implement` | Does not arise. SkipHow ships one skill and no commands, so there is no invocation flag to work around |

## The gaps 885 names are already closed here

Completion. [ADR 0004](../../decisions/0004-github-lifecycle-and-authority.md) makes the Issue the record and the pull request the delivery, and `github.md` closes or updates the Issue and anything that depended on it after confirming the merge. The dependency graph advances because the lifecycle ends at the work item, not at the commit.

Escalation. The four stop reasons are the whole escape hatch, and everything outside them becomes a ruling recorded in the handoff and the report. An item that fails twice with the same cause is retried at a higher role, and once more is `BLOCKED` on the Issue with the exact next action. Nothing waits on a terminal nobody is watching.

Machine-readable graph. `github.md` relates Issues through the tracker's own parents, sub-issues, and dependencies, which the tracker's API already exposes. ADR 0004 step 4 and [ADR 0014](../../decisions/0014-conform-to-the-tracker-classification.md) forbid using labels as a second workflow engine, which is the failure a separate text file would reintroduce.

That repository needs a declared config because its skills span GitHub, GitLab, local markdown, and Jira, where the answer is genuinely underivable. ADR 0014 recorded the same asymmetry when it rejected a per-repository tracker config for SkipHow.

## Not adopted, and what would reopen each

Two mechanics in 787 have no equivalent here. Neither clears the bar for a package change, and both are recorded with the observation that would reopen them.

An integration branch. 787 collects every worker branch on `task/<slug>` and leaves the merge to the default branch to a human. SkipHow opens one pull request per Issue against the default branch and merges it only under end-to-end authority. ADR 0004 rejected merging every successful implementation and also rejected never merging automatically, because the second would leave explicitly authorized unattended work unfinished. Reopen if a receipt shows an unattended batch landing something on the default branch that a staging branch would have caught first.

A progress signal during the run. 787 prints state transitions while the fleet works. SkipHow appends a checkpoint to `.skiphow/handoff.md` at every item boundary and reports once at the end. [Product and UX research](../2026-08-25/product-and-ux.md) rejected constant progress narration for consuming context and hiding the few updates that matter, and the owner's overnight run has nobody reading the terminal. Reopen if an owner cancels or restarts a healthy run because it looked stalled.

## What is worth borrowing

Nothing new. Borrow 7 in the [prior-art mechanics](prior-art-mechanics.md) note, native sub-issues and dependencies instead of labels as a workflow engine, already took the one mechanic from this source that SkipHow was missing, and 1.7 restored the sentence that carries it. The rest of 787 describes what `long-work.md` and `github.md` already specify, at greater length and with two constants this project rejected on purpose.

The reopening bar in the [2026-08-25 prior art](../2026-08-25/prior-art.md) note applies unchanged: a new feature list alone is not enough.

## Files read

- `https://github.com/mattpocock/skills/issues/787`
- `https://github.com/mattpocock/skills/issues/885`
- `https://github.com/mattpocock/skills` README and skill list
