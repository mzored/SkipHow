# Field audit, 2026-08-27

The second audit of real SkipHow sessions in other repositories, produced with the contributor `dogfood`
skill and recorded per [ADR 0008](../../decisions/0008-receipts-over-a-live-harness.md). Sessions are named
by id and date only; no project names, Issue titles, or paths appear here.

## What was read

Two external sessions on Claude Code 2.1.246, both on 2026-08-26, two repositories.

| Session | Plugin | Route | State |
| --- | --- | --- | --- |
| `7c5f12fa` | 1.7.0 | `DELIVER` | **live throughout the audit**; report, merge, and cleanup unscored |
| `43408b2d` | 1.9.0 | `RESPOND` | complete |

Each was judged against the bytes it ran, not against HEAD. The live session owes no report, so its report
shape and finding tags were not checked; scoring them is the easiest false positive this audit can produce.

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

## Limits

`7c5f12fa` was live for the whole audit, so its report, merge, cleanup, and finding tags are outside this
sample and need a re-read after it finishes. Findings a run noticed and silently dropped leave no trace, so
every conformance count here is an upper bound. No network calls were made: tracker and check states are the
transcripts' claims about themselves, never verified against the services.

Audited `7c5f12fa` · 595 records · plugin 1.7.0 · correct subagent models; `long-work` and `model-routing` unloaded; no handoff written
Audited `43408b2d` · 265 records · plugin 1.9.0 · read-only, five headings, tags matched the records created
