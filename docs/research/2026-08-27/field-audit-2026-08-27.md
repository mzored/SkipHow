# Field audit, 2026-08-27

The second audit of real SkipHow sessions in other repositories, produced with the contributor `dogfood`
skill and recorded per [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Sessions are named
by id and date only; no project names, Issue titles, customer data, or absolute private paths appear here.

## What was read

Three external sessions on Claude Code 2.1.246, all on 2026-08-26.

| Session | Plugin | Route | State |
| --- | --- | --- | --- |
| `7c5f12fa` | 1.7.0 | `DELIVER` | the 1,195-record sequence ended mid-tool; later records appended |
| `43408b2d` | 1.9.0 | `RESPOND` | complete |
| `35775b1d` | 1.13.0 | `DELIVER` | historical 1,413-record snapshot; later records appended |

Each was judged against the contract identity supported by its transcript evidence or an independent
exact-tree binding, never against HEAD by default. The first `7c5f12fa` read was an open sequence; the later
re-read scores only what its then-readable records can prove.

This historical audit used the digest available at the time. In the wording below, a recorded read is
positive transcript evidence; no recorded read means the digest found no qualifying successful read event.
That absence is a limitation, not proof that a body was absent from model context through every possible host
path. A governing contract is attributed to a version only from a successful root-skill injection record with
that versioned base path or an independent exact-tree binding. An unknown or unversioned contract body remains
`UNVERIFIED`.

The sections about `builder`, `reviewer`, `scout`, `model-routing.md`, and `long-work.md` describe the audited
1.x snapshots only. SkipHow 2.0 removed the fixed role files, model-routing reference, and long-work reference.
Those historical names and findings do not describe the current package topology.

## The owner was watching a version the run was not using

`7c5f12fa` opened at `19:07:21Z`, and the transcript records a successful root-skill injection at `19:07:38Z` from
`…/plugins/cache/skiphow/skiphow/**1.7.0**/skills/skiphow`. Both references it read were read from that same
directory, and a scan of the whole transcript for cached-plugin paths returns `1.7.0` twice and 1.9.0 never.
The host's install record shows 1.9.0 for that project with `lastUpdated 19:08:52Z` — 74 seconds after the
recorded 1.7.0 injection. A `/reload-plugins` at `19:14:25Z` refreshed the cache; the transcript records no
later root-skill injection.

The owner believed they were exercising 1.9.0 and reported it working noticeably better. They were watching
1.7.0. Nothing in the package caused this and nothing in the package can fix it, but it changes what a
session may be cited for: **a receipt is evidence only for a contract version bound by its own transcript or
by independent exact-tree evidence.** The `dogfood` digest already derives the version from the injected
path, which is why the mistake was visible at all.

## The audited 1.x model routing resolved at runtime

`7c5f12fa` spawned eight delegates and passed no `model` override on any of them. The models the host
actually ran:

| Role | Spawns | Model observed |
| --- | --- | --- |
| `builder` | 5 | `claude-sonnet-5` |
| `reviewer` | 3 | the session model (`claude-opus-5`) |
| `scout` | 0 | — |

The 1.7 agent definitions resolved every one. This was the first field observation that
[ADR 0007](../../decisions/0007-host-adapters-for-routing-and-continuity.md) and
[ADR 0009](../../decisions/0009-reviewer-inherits-and-one-engineering-reference.md) work at runtime rather
than on paper: earlier research recorded that "every subagent runs on the owner's main model" and "the tiers
are documentation". They were not in that package. The three agent files are byte-identical between 1.7.0
and 1.9.0, so the receipt carried to the audited 1.9.0 snapshot. It does not carry to 2.0, which has no fixed
role files.

`scout` going unused is not a deviation. It ships without `Bash`, and the root's own bounded lookups were
shell calls it could not have made.

## The audited 1.x delegation rules had no recorded reference read

The historical digest found no qualifying successful `model-routing.md` read across eight delegations. In the
first two audit sets that is **5 of 5** delegating sessions without positive read evidence, and the governing
sentence is byte-identical in every audited version there: 1.6.1, 1.7.0, and 1.9.0. The later 1.13 follow-up
below is a separate review-trigger finding against different governing bytes and is not folded into that
denominator.

The consequence was nothing visible, and that is the finding. The tier table is redundant with the agent
descriptions the host already lists, so a run picks the right role without it. What the file held alone was
the brief contract and the failure-escalation ladder — the two rules
[ADR 0016](../../decisions/0016-decomposition-needs-a-trigger-a-run-can-evaluate.md) said the next receipt
should measure. `DEFECT` in the layout, not in the run: rules that bind unconditionally were sitting in a
file for which qualifying successful reads were not observed reliably. Both moved to the root in 1.10.0 and the ADR was amended. SkipHow
2.0 later removed the fixed role and model-routing machinery rather than carrying that architecture forward.

## An audited 1.x decomposed run had no recovery artifact

The historical digest likewise found no qualifying successful `long-work.md` read, though every trigger fired:
a fixed queue of five tracker items, parallel
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

- **One stop to ask, on the right thing.** The run reached two protected actions, production work and a public
  release, and asked once with the alternatives stated. Everything else was ruled and carried on.
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

## The 1,195-record re-read of `7c5f12fa`

The sections above were written from an open 595-record sequence. The then-readable sequence continued through
`22:34:34Z` and ended on an unmatched tool call:
**1195 records, eleven delegations, five tracker items worked.** The counts above are the earlier snapshot, not
the 1,195-record re-read. Nothing in them reverses; the queue only got longer.

**The report expectation and cause are `UNVERIFIED`.** The 1,195-record sequence ends mid-tool, with none of
the five headings and no finding tags. That proves only that no matching terminal event appears later in the
then-readable records; it does not establish why activity ended or whether a report had become due. The audit
therefore declined to score the missing report rather than infer either an excuse or a failure.

**Merge and cleanup conformed, and those are scoreable.** Three items reached the integration branch by merge
commit. Two were then reopened by the run itself, each with a comment stating that only the repository half
had landed and naming what still needed a vendor cabinet, a mail panel, and DNS — declining to close what it
could not finish rather than reporting done. Two Issues were created for findings met on the way. Two further
branches were still in review when the snapshot ended. Unowned uncommitted work on a local branch was flagged and left
untouched, with the reason it existed only locally and that the run's own verification dispatcher had been
executing from it.

**The handoff count, with its honest denominator.** At that point, across the four-session 2026-08-26 audit
and the original two-session pass here, `.skiphow/handoff.md` had been written **0 times in 6 sessions**. That
number is weaker than it looks: the long-work trigger genuinely applied in **1 of those 6**. The other five
owed no checkpoint under their exact bytes; one was a large undecomposed request whose trigger defect the
prior audit records. The
applicable sample is one session — the one already ruled above as a receipt request against 1.9.0.

What the re-read adds is that the run was not unaware of the file. Its **first command of the session** was
`cat .skiphow/handoff.md`. It checked, found nothing, and never wrote one, across five item boundaries. The
read side reached it and the write side did not. That does not change the ruling above: the transcript contains
positive `delivery.md` read evidence, and at 1.7.0 that file carries the same "read long work for a selected
queue" trigger. Whether every byte of the reference body reached model context is not independently proved;
the observed behavior is `VARIANCE` at best and `UNVERIFIED` in a single session, never a defect in the
reference body.

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
counter that looks like a budget measures something else by roughly fortyfold. The conclusion is
unchanged and the rejection stands on its other ground — a hook cannot know the agent's state. It is also moot
here: five item boundaries passed long before context was a question, and the existing rule would have produced
a checkpoint hours earlier.

`NOT-A-DEFECT` for the missing compaction checkpoint. The threshold figure is one observation on one host build
and one model — evidence that a threshold exists, not a constant.

## ADR 0004 and the audited 1.x template disagreed

Found while checking the above. [ADR 0004](../../decisions/0004-github-lifecycle-and-authority.md) says a
handoff records scope, current authority and restrictions, accepted decisions, queue, exact GitHub and Git
state, owned resources, last external result, evidence, blockers, and next safe action. The template in
the audited 1.x `long-work.md` shipped eight fields and omitted accepted decisions, owned resources, last
external result, and evidence. Both were current text when this finding was recorded. Version 1.14.0 later
aligned the template with ADR 0004; SkipHow 2.0 then removed `long-work.md`. This is historical evidence rather
than a claim about the current package. `UNSAVED`:
outside that audit's request and no record was created.

## How this re-read was checked

Its first draft ruled the read/write placement a `DEFECT` and proposed narrowing the checkpoint template to
four fields. That draft went through the 1.12 cross-host rung — one read-only `codex exec` pass at `high`,
given the package, the ADRs' rejected alternatives, and the budgets — and did not survive. The recorded
`delivery.md` read undercut the defect ruling; ADR 0004 rather than ADR 0007 owns the template; and
`long-work.md` uses the handoff precisely where the host cannot resume, so it cannot assume the tracker is
reachable. Every factual correction it made was verified against the files afterwards and all of them held,
including two errors of fact in the draft's own reading of the repository. First use of that rung on an audit
rather than on a diff, and the first time it caught a wrong ruling rather than a code defect.

## Limits for the first two sessions

`7c5f12fa`'s report-state evidence, merge, cleanup, and finding tags were outside the first pass and are
supplied by the re-read above; the sections written from the open sequence keep their snapshot counts. Findings a run noticed
and silently dropped leave no trace, so every conformance count here is an upper bound. No network calls were
made: tracker and check states are the transcripts' claims about themselves, never verified against the
services.

Audited `7c5f12fa` · 1195 records · plugin 1.7.0 · historical re-read: merge and cleanup conformed; report expectation and cause unverified; handoff still unwritten
Audited `43408b2d` · 265 records · plugin 1.9.0 · read-only, five headings, tags matched the records created

## Follow-up delivery audit: shared-checkout completion was not safe completion

Session `35775b1d` ran plugin 1.13.0 on model `claude-opus-5`, beginning with one UI request. Later owner turns
added six independently landable or systemic items. The run kept one lane. The historical digest found no
qualifying successful read of the repository, delivery, long-work, engineering, GitHub, or model-routing
instructions that governed the resulting work, and no positive evidence that the target repository's root
contributor instructions were read before files changed. Those absences do not prove an unobserved host path
could not have supplied text.

The only review was a same-host `reviewer` pass over the original candidate. It found four real defects, which were fixed, but the fix received no second review. The other installed host was authenticated and exposed its review command, but no cross-host pass ran. The target repository required Issue-linked branches; no matching Issue or pull request was created.

Another session changed and reset the shared checkout while this run was working. The run then force-restored files from the index, lost its own stylesheet change plus another lane's changes, recovered them from a patch, and eventually created the final corrective commit through a temporary index, `commit-tree`, and a direct ref update. An earlier platform-specific command failure also produced a temporary empty commit before the ref was rolled back. The final commit exists and contains the intended files, but required full repository checks were not run against that exact final candidate.

`DEFECT`: the 1.13 root `SKILL.md` did not require repository instructions before mutation or re-size after each owner turn. `DEFECT`: the widened-review trigger lived only in `references/engineering.md` and `references/model-routing.md`, for which this transcript contains no qualifying successful read evidence. `DEFECT`: the root required a commit but named neither checkout-identity guards nor the forbidden low-level completion paths, and no worktree reference existed. `NOT-A-DEFECT`: the agent can create commits; the unsafe environment and completion path made ordinary committing unreliable. `UNVERIFIED`: no 1.14 run yet proves the replacement worktree, integration, conflict, and review loop is followed.

Audited `35775b1d` · 1413 records · plugin 1.13.0 · model `claude-opus-5` · owner-turn expansion bypassed long-work and repository policy; shared checkout collision corrupted delivery

The `7c5f12fa` 1,195-record and `35775b1d` 1,413-record entries are historical audit snapshots. `7c5f12fa`
later resumed and reached 4,868 records; `35775b1d` later had records appended and reached 1,632. The census
below supersedes those counts and, for `7c5f12fa`, the earlier single-version identity for census purposes; it
does not rewrite rulings made from the evidence available at each historical snapshot.

### Limits

The follow-up audit read the 1,413-record snapshot and local Git evidence. Target GitHub state and required-check results are the run's claims about themselves, not independently verified remote state. Package changes motivated by the session were not runtime proof at that point. Later installed 1.14.2 sessions do not complete a control for this replacement-worktree, integration, conflict, and review-loop behavior, which remains `UNVERIFIED`.

## Same-day Claude Code census: 37 root owner-chat candidates, 18 other-project sessions in scope

The owner then asked for every same-day session with SkipHow use. The contributor tool can discover Claude
Code transcript files; it does not enumerate Codex desktop tasks, so this census is explicitly limited to
the Claude Code transcripts visible to `sessions.py`. The earlier four-session snapshot was incomplete, and
the two historical transcripts named above had acquired later records. The tool now selects literal
timestamped SkipHow marker records by the configured local date, reports undated marker records separately,
makes no activation inference from a marker, and does not hide a candidate because of its CWD.

The fail-closed `--on 2026-08-27` result contains **37 root owner-chat candidates**. Seventeen aggregate
observable evidence from one or more logs under that owner's host-defined `subagents/` directory; those logs
are evidence about the root chat's scope and freshness, not extra owner sessions. The other 20 have root-only
evidence. Fifteen candidates have every observed root CWD inside the SkipHow repository and therefore belong
to contributor self-development, outside this other-project dogfood audit. Four others have no observable
owner turn and no attributable contract; they remain visible candidates but are not scored as owner chats.
This scope decision uses the records themselves, not a temp-directory or first-CWD exclusion. The remaining
**18 other-project owner sessions** are the field set below: 16 have a marker timestamp on August 27; two have
only August 26 timestamps plus undated marker records, so their date membership is unverified rather than
silently excluded:

| Session | Observable contract identity | Relevant shape |
| --- | --- | --- |
| `0df7f9b0` | 1.6.1 | date-unverified adjacent session; all timestamped records are August 26 |
| `63ef1e3e` | 1.7.0 | date-unverified adjacent session; all timestamped records are August 26 |
| `a93adf29` | unknown | delivery work; not attributable to a SkipHow version |
| `fad2e98b` | 1.10.0 | CI virtual-machine lifecycle |
| `ef145001` | partially unknown: 1.12.0 plus unknown | systematic UI-card migration |
| `934e672b` | unknown | live UI work; not attributable to a SkipHow version |
| `35775b1d` | 1.13.0 | UI request expanded across concurrent checkout work |
| `189724da` | 1.13.0 | feedback-system audit and delivery |
| `3c623e6f` | unknown | live UI work; not attributable to a SkipHow version |
| `7c5f12fa` | mixed 1.7.0 and 1.10.0 | multi-item release and deployment |
| `df29ce51` | partially unknown: 1.14.2 plus unknown | bounded live-browser UI work |
| `f4cb81a8` | unknown | live UI bootstrap; not attributable to a SkipHow version |
| `9d8005c5` | partially unknown: 1.14.2 plus unknown | the named create-choice UI request, then later owner additions |
| `b3ba968e` | partially unknown: 1.14.2 plus unknown | Git cleanup and requested Codex review |
| `c263bf24` | 1.14.2 | production deployment and CI migration |
| `69e0c765` | unknown | short delivery exchange; not attributable to a SkipHow version |
| `c7d44843` | 1.14.2 | explicitly requested unattended orchestration and production delivery |
| `1d13e611` | 1.14.2 | staging delivery, then explicitly requested unattended orchestration |

The two date-unverified sessions are retained in the receipt but are not scored as August 27 behavior. Both
are closed August 26 visual sessions with a single known contract and no unreadable records; their undated
markers are why absence from August 27 cannot be proved mechanically.

Among the 16 confirmed-day candidates, five have unknown contract identity. `7c5f12fa` contains two observed
plugin versions in one long transcript, so its governing contract identity is mixed and its final behavior
cannot be assigned to one version. Four more expose one known version plus an unknown contributor; nearby
versioned bytes do not make that identity exact. Six confirmed-day candidates have one exact observed version
identity and one exact body identity. Exact body observation still does not prove which mechanism selected
the skill, so this audit does not silently upgrade body provenance to causal activation.

This is a candidate census, not an activation rate. It also corrects the date boundary without pretending
that a marker proves SkipHow governed the turn.

### The two bounded UI sessions repeated the missing routine endpoint

Six candidates contain observed 1.14.2 evidence, but they do not form one comparable or uniformly attributable
population. Three have an exact single observed identity; three also contain an unknown contributor. Two are
bounded live-UI sessions, one was explicitly about Git cleanup and Codex review, one was a production
deployment, and two explicitly asked for an orchestrator, subagents, worktrees, review, merge, and deployment.
The last four cannot answer whether a simple visual request acquired universal process it did not ask for.

The two UI sessions are the comparable pair for the narrower routine-endpoint question. Both contain complete
1.14.2 root bytes, and that body says a project-change request grants ordinary commits and routine delivery,
says not to ask for those mechanics, and reserves owner questions for promotion or a material product choice
evidence cannot settle. Both transcripts also contain an unversioned contributor, however, so neither exact
governing identity can be assigned solely to 1.14.2. Both runs left the authorized work uncommitted and asked
the owner when to branch, batch, or commit it. Neither transcript records compaction.

Observed endpoint failure, repeated **2 of 2 comparable sessions**; package causality is `UNVERIFIED`. This is
not a performance rate and does not establish a general failure probability. It does show why adding another
Git sentence to the already dense 1.14 root would be a poor response: the intended sentence was present in
both records, while exact governing identity remained unsettled. The finding fires
[ADR 0017](../../decisions/0017-autonomous-routine-delivery-uses-owned-worktrees.md)'s accepted revalidation
trigger and is acted on architecturally in
[ADR 0018](../../decisions/0018-autonomous-kernel-and-independent-task-skills.md).

### What the named create-choice session proves

The exact first request was the owner's create-choice interaction. Work began at about 09:58Z; the
implementation, focused checks, and live visual pass for that first item were substantially complete by about
10:10Z, roughly twelve minutes. Later owner turns added several more items. The whole session ran until
11:08Z, so reporting its total duration as the cost of the first button change would be false.

The session explicitly invoked an Impeccable UX workflow, used live browser iteration, and made 203 shell
calls. The other applicable UI session also explicitly invoked live Impeccable work and made 103 shell calls.
Those counts are confounded by the selected visual workflow and, in the latter session, a wait or poll. There
is no paired run without SkipHow. This audit therefore makes no causal claim about speed, token use, or tool
count.

The named session later produced substantial check evidence but still said all work remained uncommitted.
The first change was not a half-hour implementation failure; the routine local endpoint was still a genuine
failure after the implementation succeeded.

### Other same-day failures and non-comparable work

`fad2e98b` is direct evidence for the nontechnical-owner seam in 1.10.0. The agent asked the owner whether to
reverse an automatic-start principle and how many minutes an idle CI VM should remain alive. The owner
answered that both were technical decisions they could not make. The agent then chose and implemented them.
The result was eventually committed and well tested, but the two unnecessary owner questions were already a
failure for the intended product interface.

`b3ba968e` records a separate agent-mechanics failure. The owner explicitly requested Codex review, so the
review itself is not unwanted SkipHow ceremony. The agent wrapped the reviewer in shell watchers waiting for
completion markers that could never be written, then kept responding to the resulting notifications after
the useful work had finished. When asked why it was still working, it correctly attributed the delay to its
own wait construction. This is an observed failure, but not evidence that the SkipHow contract caused it.

`ef145001` took a systematic 1.12.0 visual request across every matching surface, made 292 shell calls, used a
scout and reviewer, and ended with two commits plus broad checks. The owner explicitly asked to find and fix
the pattern everywhere, so it is evidence that the old package carried substantial process, not evidence
that one isolated card required it.

`189724da` and `35775b1d` were expanded 1.13.0 deliveries. The former compacted, made 404 shell calls, used
eight delegates, and delivered a feedback pipeline after the owner explicitly widened the task. The latter is
the shared-checkout collision and unsafe completion case audited above. Neither is a baseline for a bounded
visual change.

`c263bf24` ended as a successful production deployment after a five-hour infrastructure investigation, 253
shell calls, seven delegates, compaction, and several owner decisions about paid or upgraded infrastructure.
Production and spend are protected, and the owner changed the infrastructure choice during the run. Its
procedure is not scored as overprocessing a simple request.

`c7d44843` and `1d13e611` explicitly asked for orchestration, subagents, Codex review, worktrees, merging, and
deployment, so their delegation load cannot be blamed on an implicit SkipHow fast path. `1d13e611` remains a
static open sequence. `c7d44843` later reached a terminal root response after compaction and 61 successful
structured delegation calls: one release was deployed with recorded live checks, a later deployment stopped
before changing production, and the response left part of the requested queue unfinished. The later failure
mixed an agent-introduced deployment-check error, repository dependency state, and work-environment limits;
one session cannot attribute that unfinished work to the SkipHow contract. Remote repository and
infrastructure state were not independently verified.

### Static policy had become its own workflow engine

The field verdict is narrower than the owner's overall frustration, but static comparison explains why
reinforcing 1.14 would be the wrong response. Version 1.14.2 shipped one 1,348-word root, nine references
totaling 5,090 words, three fixed delegate roles, four route names, mandatory review, model routing, worktree
and integration procedure, finding tags, tracker markers, queue and handoff schemas, and exact report
sections.

Its root-word ceiling came from repository history, not from Claude, Codex, Agent Skills, or either plugin
format: 700 words in 0.9.0, 600 in 1.1.0, 850 in 1.8.0, 1,000 in 1.10.0, and 1,400 in 1.14.0. The ceiling rose
as the accumulated policy grew. It was a maintenance accommodation, not evidence that any number improved
runtime behavior.

The selected replacement is documented in
[the 2.0 simplification note](runtime-policy-simplification.md). It removes the word ceiling, magic phrases,
routes, roles, fixed review and worktree machinery, and other procedure from the critical contract. Six clean
project-local Codex receipts cover narrow scenarios against source commit
`b2196d0bd3eeca1f542cbd8af3e1b45639aad29d` and exact owner-skill tree
`95d908988208b9fcc1d285fe1ca1c5c681c4da1b`, including the named create-choice interaction in a runnable
static fixture. Hooks were disabled, each fixture exposed exactly one project-local skill, and the logs record
the root read. These are six one-off observations of current runtime bytes, not a general success rate. The
visual run also used the user-level Impeccable skill, and none of the six proves installed-plugin behavior,
the owner's real application, Claude runtime, packaged-hook execution, or performance against a baseline.

### Limits of this same-day pass

The audit used generated digests and bounded searches over the Claude Code transcript files discoverable by
the contributor tool. It did not enumerate Codex desktop tasks and persisted no raw transcript, project
name, issue title, customer data, or private target path. Discovery retained all 37 root owner-chat
candidates and folded evidence from nested host-defined subagent logs into their roots. The 18-session field
subset is based on observed project scope and owner-turn evidence; within it, two date memberships remain
unverified, five contract identities are unknown, four are partially unknown, one is mixed, and eight are
exactly single.
`c7d44843` appended activity while this audit was running. Its current receipt freezes 4,577 records spanning
August 27 and 28; the candidate belongs to this census because its observable marker set includes August 27.
Tool calls and elapsed time are confounded
by explicitly selected live-UI workflows, deployments, owner-requested orchestration, and external waits.
Findings a run noticed and never mentioned remain invisible.

The adjacent [coverage sidecar](field-audit-2026-08-27.receipts.json) is the sole machine-readable census
record. It freezes the session token, root record count, observed plugin-version values, and evidence
fingerprint for every current census candidate. The lines below are human summaries; editing them cannot
create coverage.

Audited `6f5bc22c` · 350 records · plugin 1.6.1 · contributor self-development; outside other-project field scope
Audited `4b934d43` · 584 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `9cf18b36` · 301 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `229caa0d` · 1471 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `04a9b273` · 385 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `3d656505` · 147 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `b85ff6cb` · 154 records · plugin unknown · no observable owner turn; outside owner-chat field scoring
Audited `d67a56dd` · 115 records · plugin unknown · no observable owner turn; outside owner-chat field scoring
Audited `44222d1f` · 120 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `47b75bd2` · 140 records · plugin unknown · no observable owner turn; outside owner-chat field scoring
Audited `3c7d8179` · 166 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `f563c9d8` · 70 records · plugin unknown · no observable owner turn; outside owner-chat field scoring
Audited `203a4cb8` · 176 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `6dae1cd6` · 148 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `72ad63bd` · 203 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `c336bade` · 204 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `bf5a8c80` · 145 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `65da4d31` · 172 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `324ab17f` · 99 records · plugin unknown · contributor self-development; outside other-project field scope
Audited `0df7f9b0` · 1147 records · plugin 1.6.1 · date-unverified adjacent session; timestamped records are August 26
Audited `63ef1e3e` · 1234 records · plugin 1.7.0 · date-unverified adjacent session; timestamped records are August 26
Audited `a93adf29` · 1022 records · plugin unknown · marker candidate; contract attribution unverified
Audited `fad2e98b` · 430 records · plugin 1.10.0 · asked two engineering questions the nontechnical owner declined
Audited `ef145001` · 1218 records · plugin 1.12.0,unknown · systematic visual request completed with broad process; exact contract identity unverified
Audited `934e672b` · 353 records · plugin unknown · marker candidate; contract attribution unverified
Audited `35775b1d` · 1632 records · plugin 1.13.0 · expanded delivery collided with shared-checkout work
Audited `189724da` · 2200 records · plugin 1.13.0 · complex feedback delivery; not comparable to bounded UI work
Audited `3c623e6f` · 883 records · plugin unknown · marker candidate; contract attribution unverified
Audited `7c5f12fa` · 4868 records · plugin 1.7.0,1.10.0 · mixed contract identity; not scored to one version
Audited `df29ce51` · 551 records · plugin 1.14.2,unknown · bounded UI work left uncommitted and returned Git mechanics; exact contract identity unverified
Audited `f4cb81a8` · 74 records · plugin unknown · marker candidate; contract attribution unverified
Audited `9d8005c5` · 1093 records · plugin 1.14.2,unknown · named UI item took about twelve minutes; final work remained uncommitted; exact contract identity unverified
Audited `b3ba968e` · 1530 records · plugin 1.14.2,unknown · self-inflicted review watcher waited for impossible markers; exact contract identity unverified
Audited `c263bf24` · 1810 records · plugin 1.14.2 · production deployed after a protected infrastructure investigation
Audited `69e0c765` · 108 records · plugin unknown · marker candidate; contract attribution unverified
Audited `c7d44843` · 4577 records · plugin 1.14.2 · owner explicitly requested heavy unattended orchestration through review, integration, and production delivery; one release was deployed with recorded live checks, a later deploy stopped before production mutation, and the terminal response left remaining work unfinished
Audited `1d13e611` · 1665 records · plugin 1.14.2 · owner explicitly requested staging and heavy orchestration

Census summary · 37 root owner-chat candidates retained · 17 include nested subagent evidence · 20 are root-only · 15 contributor-scope · 4 without an owner turn · 18 other-project owner sessions scored · 16 confirmed-day plus 2 date-unverified · 8 exact-single contract identities · 4 partially unknown · 1 mixed · 5 unknown · 0 unreadable records
Bounded UI pair with observed 1.14.2 plus unknown contributions · 2 of 2 left ordinary work uncommitted and returned routine Git mechanics to the owner · package causality unverified
Current owner-skill receipt · named create-choice fixture reached 4 of 4 browser tests, rendered inspection, clean commit, no owner question
