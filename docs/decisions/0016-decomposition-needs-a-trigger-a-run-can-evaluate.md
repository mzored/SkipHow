# ADR 0016: Decomposition needs a trigger a run can evaluate

## Status

Accepted in 1.9.0, amended in 1.10.0 (see the amendment below). Amends [ADR 0006](0006-host-native-campaign-and-engineering-policy.md) by stating the
trigger it left unstated: 0006 defines how a campaign queue is run, never what makes a request one. Follows
[ADR 0015](0015-unconditional-invariants-live-in-the-root.md) (unconditional rules live in the root). [ADR 0004](0004-github-lifecycle-and-authority.md) and
[ADR 0003](0003-semantic-model-routing.md) stand.

## Date

2026-08-26

## Context

A session at 1.7.0 received fifteen owner corrections in one request, three of them marked systemic by the
owner and spanning shared surfaces. It made 216 shell calls, 26 mutations, and three commits in 87 minutes,
in one root agent. Its single delegation was a reviewer spawned after the work was already committed. Nothing
in the transcript mentions delegation, parallelism, a worktree, or a sub-issue at any point
([field audit](../research/2026-08-26/field-audit-2026-08-26.md)).

The capability was not missing. The [parallel orchestration survey](../research/2026-08-26/parallel-orchestration-proposals.md)
had already mapped an external orchestrator proposal mechanic by mechanic onto `long-work.md` and `github.md`
and concluded that SkipHow specifies all of it: decomposition into bounded units, dependency-ordered
readiness, one delegate per unit in its own worktree, serialized integration. That conclusion was right about
the text and wrong about the runtime, because in the one real batch the audit has seen, none of it ran.

The reason is the trigger. `long-work.md` opened with "when the work covers a selected queue", and the root's
reference list said "for a selected queue". A queue is defined inside `long-work.md`. A run therefore had to
know what a selected queue was in order to decide whether to open the file that defines it, and the sentence
that describes decomposing one owner request into bounded units sits behind the same door. The trigger was
circular, so it never fired.

Every other sentence the package spends on the subject points one way: "no Issue, plan, branch, or subagent",
"delegate only when isolation or parallel work pays for the transfer", "work that fits the current context
stays in it", "a large diff alone does not". Each is defensible on its own. Together they gave a run a
well-specified brake, a well-specified procedure, and nothing in between that names when to move from one to
the other.

This is the third time a rule has been present in the package and absent at runtime.
[ADR 0014](0014-conform-to-the-tracker-classification.md) records step 4 of ADR 0004 compressed out of the
shipped reference for six releases; ADR 0015 records the merge boundary living only in a file that did not
load. Here the file loads on a condition it alone defines.

## Decision

- The root names the negative case, not only the positive one. A request is not bounded when it lists several
  items that could each land and be verified on their own, or when the owner calls a change systemic. The run
  splits it into those units before starting any of them.
- The trigger for `long-work.md` becomes a property a run can evaluate before opening the file: a request
  carrying several deliverable items. The external wait, unattended work, and recovery triggers are unchanged.
  `long-work.md` opens on the same condition, and "a large diff alone does not" becomes "one large item does
  not", which is what it always meant.
- The selected queue explicitly includes the items the owner listed in the request, alongside Issue numbers, a
  batch marker, and the inbox records. Decomposition produces bounded units that each fit one delegate,
  sub-issues when the tracker supports them, rather than requiring an Issue per unit on a tracker that has no
  place to put one.
- Delegates never hold credentials and never write to remote systems moves into the root. It is an
  unconditional safety invariant that applied whenever a delegate existed, and it lived only in
  `long-work.md` and `model-routing.md` — the two references that have never both loaded in the field. Per
  ADR 0015 those references stop repeating it.

## Consequences

The root grows from 732 to about 794 words against the 850-word budget, and `long-work.md` and
`model-routing.md` each lose the sentence the root now carries.

More runs will decompose, and therefore more runs will delegate. That is the intended effect and it is also
the risk: `model-routing.md` has not loaded in 4 of 4 delegating sessions the audit has read. The role-naming
rule and the credential rule are now both in the root, which covers the two ways a delegation can be unsafe
without that file. The tier table, the brief contract, and the escalation ladder remain conditional detail,
and whether they reach a run that decomposes is the first thing the next receipt should measure.

The change does not adopt an orchestrator, an integration branch, or a progress stream. The
[parallel orchestration survey](../research/2026-08-26/parallel-orchestration-proposals.md) rejected those on
their own evidence and this ADR does not disturb that. It changes when the existing procedure is reached.

## Amendment, 1.10.0

The Consequences above ended by naming what the next receipt should measure: whether the tier table, the
brief contract, and the escalation ladder reach a run that decomposes. The
[2026-08-27 field audit](../research/2026-08-27/field-audit-2026-08-27.md) measured it. They do not.

A session decomposed an owner request into eight delegated units across isolated worktrees and never loaded
`model-routing.md`, which makes it 5 of 5 delegating sessions. It routed correctly anyway: the shipped agent
definitions carry the tier in their own descriptions, so a run picks `builder` or `reviewer` from the host's
agent listing without the reference. The observed models were `claude-sonnet-5` for every builder and the
session model for every reviewer — the first field evidence that
[ADR 0007](0007-host-adapters-for-routing-and-continuity.md) and
[ADR 0009](0009-reviewer-inherits-and-one-engineering-reference.md) resolve at runtime.

So the tier table loses nothing by staying conditional; it is redundant with the agent descriptions at this
host. The brief contract and the escalation ladder are not redundant with anything, and they were reaching no
one. Both move into the root beside the delegation sentences, and `model-routing.md` stops repeating them per
[ADR 0015](0015-unconditional-invariants-live-in-the-root.md). The reference keeps what is genuinely
conditional: which tier a job needs, the Codex spawn mechanics, and the effective-model rule.

This does not fix the loading trigger, and it is not meant to. It removes the two rules whose absence had a
cost from the file that does not load.

## Rejected alternatives

- **Move the decomposition procedure into the root.** It is conditional detail by any reading — most requests
  are one item — and it would cost roughly 200 words in the surface that loads on every request. ADR 0015's
  rule is that unconditional rules go to the root, not that unreached rules do. The trigger was the defect.
- **Trigger on size instead: diff size, file count, or estimated duration.** None is knowable before the work
  starts, which is when the decision has to be made. `long-work.md` already rejected diff size in its own
  first paragraph, and that sentence was right.
- **Ask the owner whether to decompose.** The owner decides direction, priority, and scope; how many units the
  work is cut into is an engineering decision, and ADR 0006 already rejected asking for run mode and worker
  counts as portable product constants.
- **Leave it and let the model judge.** This is what 1.7.0 did. One session is one observation, but the
  session's own transcript shows the alternative was never considered rather than considered and declined,
  which is the signature of a missing trigger rather than a judgment call.
- **Count items numerically ("three or more items").** A number invites gaming the boundary and does not
  survive a request that is one sentence and three weeks of work. "Items that could each land and be verified
  on their own" is the property that actually matters.

## Revalidation triggers

Revisit when a receipt shows a run decomposing a request that should have stayed one unit, when a receipt
shows the new trigger firing on a request the owner considered bounded, when a decomposed run loses selected
work that a single pass would have finished, or when a receipt shows a delegation made without a brief or a
third failure worked past without `BLOCKED` — the two rules the 1.10.0 amendment moved into the root.

The "still did not load `model-routing.md`" trigger is retired by that amendment: it fired 5 of 5 times and
the answer each time was that the reference held nothing the run needed. What remains in it is conditional
detail, so its loading is no longer evidence of anything.
