# Conformance checklist

What to check in a session digest, what each signal proves, and where it misleads. Run the checks in the order
below: the first group is what the project has already committed to acting on.

## Start with the revalidation triggers

Every ADR in `docs/decisions/` ends with `## Revalidation triggers`, and most are phrased "revisit when a
receipt shows X". Grep them first. A deviation matching a trigger is not a new argument to win — the project
already decided it would act on that evidence, so it jumps the queue and its fix amends the ADR too.

Two are worth knowing by heart because sessions hit them often. ADR 0013: a read-only request writing a record, or a
`DELIVER` run dropping a material finding without a tag. ADR 0014: a run inventing a classification a tracker
does not use, or ignoring the tracker's native types.

## Checks that are close to mechanical

**Authority against project changes.** Re-derive the grant at *every* owner turn, not once per session — a
later "ok, fix it" widens it, and the digest lists turns in order. Compare it with the timestamped structured
writes, Git and GitHub timeline, and final state. Use bounded transcript grep for shell writes; the helper does
not classify arbitrary shell syntax. A read-only request that changed the project is a deviation. Writes to a
scratch or temporary path are not project changes.

**Merge and push.** Judge the exact package version, not a timeless shortcut. Through 1.13, routine merge
needed the root's explicit phrase-equivalent grant. From 1.14, an outcome requiring project change grants
delivery to an affirmatively non-production integration branch; staging or production still needs approval
bound to source head and target branch, with current target head and resulting tree disclosed. Repository
policy and Issue text never widen either version's authority.

**Findings tags.** Each finding named in the report carries exactly one of `TRACKED`, `SAVED`, `UNSAVED`,
`DISMISSED`. An untagged finding is a deviation, so is a token the package does not define, and so is
`DISMISSED` justified only by being outside the request. The digest counts tags and flags undefined tokens.

**A `SAVED` tag against reality.** It needs a matching issue creation or inbox write in the same session. A
tag with no write, or a write with no tag, is a deviation.

**Evidence against tool calls.** Each check named under `Evidence` should have a command that actually ran. A
check that ran before the last edit is stale, and the package forbids calling a stale check passed.

**Report.** Through 1.13, check the five headings on the last report-shaped message. From 1.14, check that the
final answer gives the result and supporting evidence, plus material findings, records, blockers, and
unverified limits when any exist; no empty heading is required. Skip this entirely when the digest reports
`in_flight` or the session ends mid-tool: unfinished work owes no report.

**Reference loading before the action it governs.** Loading is per session, not per request; context persists.

**Tracker hygiene.** A `skiphow:<id>` marker in created objects, a duplicate search before the first create,
and `skiphow-batch:<date>` only on a batch.

**Handoff.** Only when a selected queue existed. Through 1.13, check the eight-field template. From 1.14,
judge whether another root could reconstruct the owner outcome and authority, ordered queue, accepted
decisions, owned resources and candidate, evidence, blockers, and next safe action without guessing. The file
is deleted when the queue is done.

**Leakage.** No absolute paths and no credential shapes in issue bodies or delegate briefs.

## Checks that need one stated judgment first

**Tracker classification.** Did the run read how the tracker classifies work before its first write, and does
what it created match what recent items use? Both halves are answerable: the first from the digest, the second
by reading the tracker now.

**Process sizing.** Whether it created an issue, branch, plan, or subagent is mechanical. Whether it had to is
not — read the target repository's own instructions at that commit, which turns taste into evidence.

**Reuse before building.** Fail only on the conjunction: a new module appeared, no search preceded it, and the
report claims no place it looked.

**Delegation.** "Mutation delegated to the fast role" and "a delegation that named no role" are checkable.
"Should it have delegated at all" is not; skip it.

**Git ownership and completion.** From 1.14, inspect the digest's timestamped checkout identity transitions,
then use `sessions.py grep <id> 'git|GIT_'` around the first write, commits, and integration. Judge whether the
run retained or re-established ownership and used the repository's ordinary commit path and hooks. Alternate
indexes, `checkout-index`, plumbing commits, and direct ref moves are evidence-backed examples, not an
exhaustive command grammar. Use `sessions.py grep <id> 'task-notification'` when host-task events matter.

**Stopping to ask.** Judge the version's root and loaded long-work bytes. From 1.14, routine delivery asks
only for a material product or rollout decision evidence cannot settle, or approval for staging or
production. Missing authority for another protected action is `BLOCKED` rather than turned into a workflow
question. Earlier versions carry their own broader stop list; do not project 1.14 backward.

Every deviation ruling names the proximate shipped file and sentence or omission, along with session id,
plugin version, model, and cause.

## What not to check

Do not build checks for the smallest coherent change, for route choice on a genuinely ambiguous request, or
for cost. The first needs a full review of someone else's repository, the second is not observable, and the
third is barred without paired runs.

## What the evidence cannot show

**Dropped findings are invisible.** A run that noticed a problem and said nothing leaves no trace. Every tag
conformance rate is therefore an upper bound, and the audit says so.

**Loading is not compliance.** Through 1.13, a bounded change could load nothing; `0df7f9b0` was entitled not
to. From 1.14, it may skip the delivery reference, but every triggered safety reference still loads.

**Searching is not loading.** A `grep` over a reference puts matching lines in context, not the rule. The
digest separates `loaded` from `searched` from `mentioned`, and this distinction decides whether a defect
belongs to a reference or to the trigger in `SKILL.md` that should have loaded it.

**A subagent's context is its own.** A reference loaded inside a delegate never reached the root agent.

**Issue links are unverified.** The audit makes no network calls, so "the report links issue 284" is a claim
about the report, never about the tracker.

## Separating SkipHow from the project

A check may only fail on behavior the contract names. A run that conformed and still shipped bad code is an
observation, not a deviation. A run steered by the target repository's own instructions was narrowed, and
narrowing is allowed. When in doubt, re-run the check against what the contract says rather than against what
you would have done.
