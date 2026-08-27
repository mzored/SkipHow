# Field audit, 2026-08-27

The second audit of real SkipHow sessions in other repositories, produced with the contributor `dogfood`
skill and recorded per [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Sessions are named
by id and date only; no project names, Issue titles, or paths appear here.

## What was read

Three external sessions on Claude Code 2.1.246, all on 2026-08-26.

| Session | Plugin | Route | State |
| --- | --- | --- | --- |
| `7c5f12fa` | 1.7.0 | `DELIVER` | complete; first read live, then re-read after completion |
| `43408b2d` | 1.9.0 | `RESPOND` | complete |
| `35775b1d` | 1.13.0 | `DELIVER` | complete |

Each was judged against the bytes it ran, not against HEAD. `7c5f12fa` owed no report when first read because
it was live; the later re-read scores only what its completed transcript can prove.

## The owner was watching a version the run was not using

`7c5f12fa` opened at `19:07:21Z` and its skill was injected at `19:07:38Z` from
`…/plugins/cache/skiphow/skiphow/**1.7.0**/skills/skiphow`. Both references it read were read from that same
directory, and a scan of the whole transcript for cached-plugin paths returns `1.7.0` twice and 1.9.0 never.
The host's install record shows 1.9.0 for that project with `lastUpdated 19:08:52Z` — 74 seconds after the
skill body was already in context. A `/reload-plugins` at `19:14:25Z` refreshed the cache and did not
re-inject the loaded text.

The owner believed they were exercising 1.9.0 and reported it working noticeably better. They were watching
1.7.0. Nothing in the package caused this and nothing in the package can fix it, but it changes what a
session may be cited for: **a receipt is only evidence for the version whose bytes appear in its own
transcript.** The `dogfood` digest already derives the version from the injected path, which is why the
mistake was visible at all.

## Model routing resolves at runtime — the first field proof

`7c5f12fa` spawned eight delegates and passed no `model` override on any of them. The models the host
actually ran:

| Role | Spawns | Model observed |
| --- | --- | --- |
| `builder` | 5 | `claude-sonnet-5` |
| `reviewer` | 3 | the session model (`claude-opus-5`) |
| `scout` | 0 | — |

The shipped agent definitions resolved every one. This is the first field observation that
[ADR 0007](../../decisions/0007-host-adapters-for-routing-and-continuity.md) and
[ADR 0009](../../decisions/0009-reviewer-inherits-and-one-engineering-reference.md) work at runtime rather
than on paper: earlier research recorded that "every subagent runs on the owner's main model" and "the tiers
are documentation". They are not. The three agent files are byte-identical between 1.7.0 and 1.9.0, so this
receipt carries to HEAD.

`scout` going unused is not a deviation. It ships without `Bash`, and the root's own bounded lookups were
shell calls it could not have made.

## The delegation rules were reaching no one

`model-routing.md` did not load, across eight delegations. That is **5 of 5** delegating sessions across both
audits, and the governing sentence is byte-identical in 1.7.0 and 1.9.0.

The consequence was nothing visible, and that is the finding. The tier table is redundant with the agent
descriptions the host already lists, so a run picks the right role without it. What the file held alone was
the brief contract and the failure-escalation ladder — the two rules
[ADR 0016](../../decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) said the next receipt
should measure. `DEFECT` in the layout, not in the run: rules that bind unconditionally were sitting in a
file whose loading is optional in practice. Both move to the root in 1.10.0 and the ADR is amended.

## A decomposed run with no recovery artifact

`long-work.md` did not load either, though every trigger fired: a fixed queue of five tracker items, parallel
worktrees, external waits polled in-session, unattended work across fifty minutes, and an owner turn calling
the change systemic.

Measured consequence: **no handoff file was written at any point, and the repository has no `.skiphow/`
directory at all.** A fifty-minute run holding eight delegates, three pushed branches, and a fresh grant to
release had nothing that could reconstruct it.

This is the second observation of the trigger-circularity `DEFECT` recorded in the 2026-08-26 audit, and
1.9.0's rewritten trigger — "a request carrying several deliverable items" — would have fired here. It is
therefore a receipt request against 1.9.0 rather than a new change: the fix exists and has not yet been seen
working in the field.

## Acting on the host outside the project

The run modified a virtual-machine configuration file under the owner's home directory, force-stopped and
restarted that VM, and deleted regenerable caches from three cache roots plus a package-manager prune. Two
deletion batches ran before it asked the owner anything; it asked eight minutes later, and honoured the
answer for everything afterwards. The session ran with host permission prompts disabled, so no approval
existed for the earlier batches either.

The owner ruled this acceptable. Recorded as `NOT-A-DEFECT` with its ordering, because the contract's
Authority section enumerates production, payments, credentials, private data, public release, repository
settings, and irreversible deletion — every item framed on the project and its remotes — and says nothing
about the machine the run is executing on. One observation is not enough to change a contract sentence. A
second sighting has this to pool against.

## What conformed

- **One stop to ask, on the right thing.** The run reached a production path and a release, which are two of
  the four things that justify stopping, and asked once with the alternatives stated. Everything else was
  ruled and carried on.
- **Every delegation named its role**, and the root kept all remote writes to itself — including pushing a
  branch a delegate had committed but not pushed.
- **An unrelated owner edit survived.** A dirty settings file belonging to the owner was stashed for one
  dispatch and restored untouched, and the run said so.
- **Independent review earned its spawn.** Two of three reviewer delegations returned blocking defects on
  branches that were otherwise ready.
- **No merge or push to a shared branch without the grant**, so ADR 0015's second revalidation trigger did
  not fire in this session.
- `43408b2d`, the one 1.9.0 session read, produced all five report headings with two `SAVED` and two
  `DISMISSED` findings, each `SAVED` one matching a record the run actually created.

## Repeat observations

- **Absolute local paths in delegate briefs — 8 of 8.** Already ruled in the 2026-08-26 audit as
  `NOT-A-DEFECT` in the run and a defect in the rule's scope. Unchanged, still not costly, still true.
- **The host blocked a chained sleep** used to poll an external wait and redirected the run to its own
  waiting primitive. A host-behaviour note, not a package defect: the package names external waits without
  prescribing a mechanism, which is correct, but a run that reaches for chained sleeps will keep meeting this.

## The re-read, after `7c5f12fa` finished

The sections above were written while the session was live and read 595 records. It ran on to `22:34:34Z`:
**1195 records, eleven delegations, five tracker items worked.** The counts above are the live snapshot, not
the finished run. Nothing in them reverses; the queue only got longer.

**The report was never owed.** The session ends mid-tool, with none of the five headings and no finding tags.
A run that ends mid-tool owes no report, so this is not scored — scoring it is the easiest false positive this
audit could produce, which is why the first pass deferred it rather than guessing.

**Merge and cleanup conformed, and those are scoreable.** Three items reached the integration branch by merge
commit. Two were then reopened by the run itself, each with a comment stating that only the repository half
had landed and naming what still needed a vendor cabinet, a mail panel, and DNS — declining to close what it
could not finish rather than reporting done. Two Issues were created for findings met on the way. Two further
branches were still in review when it stopped. Unowned uncommitted work on a local branch was flagged and left
untouched, with the reason it existed only locally and that the run's own verification dispatcher had been
executing from it.

**The handoff count, with its honest denominator.** `.skiphow/handoff.md` has now been written **0 times
across all eight external sessions read**. That number is weaker than it looks: the long-work trigger genuinely
applied in **1 of those 8**, and the other seven were single bounded items that owed no checkpoint. The
applicable sample is one session — the one already ruled above as a receipt request against 1.9.0.

What the re-read adds is that the run was not unaware of the file. Its **first command of the session** was
`cat .skiphow/handoff.md`. It checked, found nothing, and never wrote one, across five item boundaries. The
read side reached it and the write side did not. That does not change the ruling above: `delivery.md` did load,
and at 1.7.0 that file carries the same "read long work for a selected queue" trigger. A plain instruction was
in context and was not followed, which is `VARIANCE` at best and `UNVERIFIED` in a single session, never a
defect in the reference body.

## What compaction costs, measured

The question that opened this re-read was why the run did not checkpoint as it neared the context limit. The
measurements answer it and correct a sentence in the record.

- `63ef1e3e` compacted automatically at `preTokens: 368850`, `postTokens: 15768`.
- `7c5f12fa` peaked near **355,000** context tokens and never compacted — roughly 14k short of that mark.
- The only context-budget signal either session receives is `<total_tokens>N tokens left</total_tokens>`,
  counting down from **15,000,000**. That is a session *spend* budget, not context fill: it read about
  **14.85M** at the moment `63ef1e3e` compacted with its window full, having moved about 1% across the whole
  fill.

[ADR 0007](../../decisions/0007-host-adapters-for-routing-and-continuity.md) rejected a `PreCompact` hook and
replaced "checkpoint before compaction" with "at every item boundary", on the stated ground that the model
"cannot foresee" compaction. The threshold turns out to be a real number, so that phrase is imprecise. The
accurate form is that **no calibrated in-context gauge of context fill exists in this host build**, and the one
counter that looks like a budget measures something else by two orders of magnitude. The conclusion is
unchanged and the rejection stands on its other ground — a hook cannot know the agent's state. It is also moot
here: five item boundaries passed long before context was a question, and the existing rule would have produced
a checkpoint hours earlier.

`NOT-A-DEFECT` for the missing compaction checkpoint. The threshold figure is one observation on one host build
and one model — evidence that a threshold exists, not a constant.

## ADR 0004 and the shipped template disagree

Found while checking the above. [ADR 0004](../../decisions/0004-github-lifecycle-and-authority.md) says a
handoff records scope, current authority and restrictions, accepted decisions, queue, exact GitHub and Git
state, owned resources, last external result, evidence, blockers, and next safe action. The template in
`long-work.md` ships eight fields and omits accepted decisions, owned resources, last external result, and
evidence. Both are current text. `UNSAVED`: outside this audit's request and no record was created, so the
owner can ask to save it.

## How this re-read was checked

Its first draft ruled the read/write placement a `DEFECT` and proposed narrowing the checkpoint template to
four fields. That draft went through the 1.12 cross-host rung — one read-only `codex exec` pass at `high`,
given the package, the ADRs' rejected alternatives, and the budgets — and did not survive. The loaded
`delivery.md` trigger undercut the defect ruling; ADR 0004 rather than ADR 0007 owns the template; and
`long-work.md` uses the handoff precisely where the host cannot resume, so it cannot assume the tracker is
reachable. Every factual correction it made was verified against the files afterwards and all of them held,
including two errors of fact in the draft's own reading of the repository. First use of that rung on an audit
rather than on a diff, and the first time it caught a wrong ruling rather than a code defect.

## Limits for the first two sessions

`7c5f12fa`'s report, merge, cleanup, and finding tags were outside the first pass and are supplied by the
re-read above; the sections written before it stopped keep their live-snapshot counts. Findings a run noticed
and silently dropped leave no trace, so every conformance count here is an upper bound. No network calls were
made: tracker and check states are the transcripts' claims about themselves, never verified against the
services.

Audited `7c5f12fa` · 1195 records · plugin 1.7.0 · re-read after it finished: merge and cleanup conformed, no report owed, handoff still unwritten
Audited `43408b2d` · 265 records · plugin 1.9.0 · read-only, five headings, tags matched the records created

## Follow-up delivery audit: shared-checkout completion was not safe completion

Session `35775b1d` ran plugin 1.13.0 on model `claude-opus-5`, beginning with one UI request. Later owner turns added six independently landable or systemic items. The run kept one lane and loaded none of the repository, delivery, long-work, engineering, GitHub, or model-routing instructions that governed the resulting work. It did not read the target repository's root contributor instructions before changing files.

The only review was a same-host `reviewer` pass over the original candidate. It found four real defects, which were fixed, but the fix received no second review. The other installed host was authenticated and exposed its review command, but no cross-host pass ran. The target repository required Issue-linked branches; no matching Issue or pull request was created.

Another session changed and reset the shared checkout while this run was working. The run then force-restored files from the index, lost its own stylesheet change plus another lane's changes, recovered them from a patch, and eventually created the final corrective commit through a temporary index, `commit-tree`, and a direct ref update. An earlier platform-specific command failure also produced a temporary empty commit before the ref was rolled back. The final commit exists and contains the intended files, but required full repository checks were not run against that exact final candidate.

`DEFECT`: the 1.13 root `SKILL.md` did not require repository instructions before mutation or re-size after each owner turn. `DEFECT`: the widened-review trigger lived only in `references/engineering.md` and `references/model-routing.md`, which the run did not load. `DEFECT`: the root required a commit but named neither checkout-identity guards nor the forbidden low-level completion paths, and no worktree reference existed. `NOT-A-DEFECT`: the agent can create commits; the unsafe environment and completion path made ordinary committing unreliable. `UNVERIFIED`: no 1.14 run yet proves the replacement worktree, integration, conflict, and review loop is followed.

Audited `35775b1d` · 1413 records · plugin 1.13.0 · model `claude-opus-5` · owner-turn expansion bypassed long-work and repository policy; shared checkout collision corrupted delivery

### Limits

The follow-up audit read the completed transcript and local Git evidence. Target GitHub state and required-check results are the run's claims about themselves, not independently verified remote state. Package changes motivated by the session are not runtime proof; all new 1.14 behavior remains `UNVERIFIED` pending a real installed-plugin run.

## Same-day audit: 1.14 repeated the workflow question it prohibited

The owner then asked for the external SkipHow sessions available on 2026-08-27 to be checked. The set was
frozen by date before judgment. Four sessions matched at that point; a fifth session started after the freeze
and is not silently folded into these rulings.

| Session | Plugin | Model | Snapshot state | Relevant shape |
| --- | --- | --- | --- | --- |
| `189724da` | 1.13.0 | `claude-opus-5` | complete; compacted | complex multi-part delivery |
| `df29ce51` | 1.14.2 | `claude-opus-5` | closed; no compaction | bounded live-browser UI work |
| `9d8005c5` | 1.14.2 | `claude-opus-5` | closed; no compaction | named UI session, later expanded by owner turns |
| `c263bf24` | 1.14.2 | `claude-opus-5` | in flight; no compaction | production deployment |

The two 1.14.2 UI sessions are the applicable pair for the routine-commit question, not paired performance
runs. The exact root bytes were in context in both. They say a
project-change request grants ordinary commits and routine delivery, say not to ask for those steps, and
limit owner questions to promotion or a material product choice evidence cannot settle. Nevertheless, each
run left routine authorized work uncommitted and asked the owner when to branch, batch, or commit it. Neither
session compacted.

`VARIANCE`, repeated **2 of 2 applicable sessions**. The governing language was explicit and byte-identical;
the proximate cause is not a missing sentence in a reference. This also fires
[ADR 0017](../../decisions/0017-autonomous-routine-delivery-uses-owned-worktrees.md)'s accepted revalidation
trigger for a 1.14 run asking about routine delivery mechanics. The trigger is acted on in
[ADR 0018](../../decisions/0018-autonomous-kernel-and-independent-task-skills.md), but not by adding another
Git step: the existing step was already ignored.

### What the named UI session does and does not prove

The first named request was one small UI decision and presentation change. Work on that initial change began
at about 09:57Z and the implementation, focused checks, and live visual pass were substantially complete by
about 10:10Z, roughly twelve minutes. Later owner turns added six more items and expanded the session. Its
total elapsed time therefore cannot be reported as the cost of the initial request.

The session explicitly invoked an Impeccable live-UI workflow, used a live browser loop, and made 203 shell
calls in the snapshot read for this audit. The other 1.14.2 UI session also explicitly invoked Impeccable and
live iteration, included a long wait or poll, and made 103 shell calls. Those counts describe the sessions;
they do not isolate SkipHow's contribution. There is no paired run without SkipHow, so the audit makes no
speed, token, or cost claim. The supported finding is narrower and more important to the owner: after all
that work, both sessions still handed routine commit mechanics back to them.

The named session later closed with a result and substantial check evidence. Its final text still stated that
all work was uncommitted. The routine question and incomplete local endpoint are therefore both scoreable;
they are not inferred from a live missing report.

### The other two sessions are not evidence for a universal fast path

`189724da` ran 1.13.0 for a complex multi-part change, compacted, made 404 shell calls, and used eight
delegations. It eventually reviewed and pushed to a non-production integration target after a later owner
turn supplied the version's phrase-based authority. The 1.14 package had already removed that phrase token,
so this older session cannot prove that current wording still needs one. Its scale also makes it a poor
baseline for a bounded visual edit.

`c263bf24` was an in-flight production deployment. It loaded the delivery, GitHub, long-work, and worktree
references and used four reviewer delegations. Production work is explicitly protected and can justify more
gates than a visual change. The missing model-routing load is one unfinished observation and remains
`UNVERIFIED`; it is not evidence that the deployment overprocessed, and no report was owed while it was live.

### Static policy had become its own workflow engine

The field verdict above is variance, but a separate static comparison explains why reinforcing 1.14 would be
the wrong response. Version 1.14.2 shipped one 1,348-word root, nine references totaling 5,090 words, three
fixed delegate roles, four route names, mandatory review, model routing, worktree and integration procedure,
findings tags, tracker markers, queue and handoff schemas, and exact report evidence.

Its root-word ceiling was not imposed by Claude, Codex, the Agent Skills specification, or either plugin
format. Repository history raised the local number from 600 in 1.2.0 to 850 in 1.8.0, 1,000 in 1.10.0, and
1,400 in 1.14.0 as the policy grew. The corresponding artifact grew with it. This is a design constraint
tracking accumulated text, not host evidence that those four numbers are useful.

The result is not scored as a package `DEFECT` caused by the two sessions; their failed sentences were plain.
It is the architecture the owner explicitly asked to replace, supported by the analogue and host research in
[the 2.0 simplification note](runtime-policy-simplification.md). The new candidate remains `UNVERIFIED` until
real installed-plugin receipts show the thinner owner skill and focused methods working.

### Limits of this same-day pass

The audit used generated digests and bounded transcript searches. It persisted no raw transcript, project
name, issue title, customer data, or private target path. The production snapshot can gain records after this
count. Tool calls and elapsed time are confounded by explicitly selected live-UI workflows and external
waits. Findings a run noticed and never mentioned remain invisible.

Audited `189724da` · 2200 records · plugin 1.13.0 · complete complex delivery; not comparable to a bounded 1.14 UI change
Audited `df29ce51` · 551 records · plugin 1.14.2 · closed UI run; routine work left uncommitted and mechanics returned to owner
Audited `9d8005c5` · 1093 records · plugin 1.14.2 · closed UI run; initial change about twelve minutes, later additions expanded it, final state explicitly uncommitted
Audited `c263bf24` · 873 records · plugin 1.14.2 · live production snapshot; heavy procedure not scored as overprocessing
