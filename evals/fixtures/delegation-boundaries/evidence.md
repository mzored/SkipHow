# Delegation boundary decisions

These independent scenarios are invented. Recommend engineering actions using the supplied evidence.
Do not execute them or treat their workspaces as present on disk.

## Independent repairs

A retained compiler report identifies 180 errors in 90 test files across orders, catalog, and accounts.
One shared typed fixture factory is missing a required field; fixing that accounts for 60 errors across
all three areas. The remaining 120 errors are heterogeneous mock and assertion mismatches local to
each area. The report already groups each diagnostic by cause and area. Each area's tests and compiler
diagnostics can be checked independently; a combined typecheck establishes final acceptance. Compiler
settings and test semantics must remain intact. No API migration or compatibility transition is involved.

The shared factory and compiler configuration must have one writer at a time. Writer isolation and
capacity are available for three lanes, but parallelism is optional. Every proposed assignment must be
small enough to implement, verify, and review from its record. Repairing test types, extending coverage
to previously unchecked browser tests, and wiring new gates are distinct outcomes; only the first is
requested here. The existing inventory is sufficient to choose the next useful boundary.

## Uniform transformation

An existing repository codemod replaces one deprecated import in 240 files. Its dry run shows only
that import changing, with no shared type or behavior changes. The existing exact-output checker and
compiler cover the whole transformation; a prior check on the same inputs completed within a minute.
The patch is uniform and reviewable as one change. No other writer touches these files. Splitting by
directory would repeat the same setup and checks without reducing an identified risk. Correct replacement
everywhere, unchanged runtime behavior, and a checked diff are the requested outcome.

## Outgrown assignment

A delegate was assigned to repair one parser's eight cases against a documented wire format, preserving
compatibility. Its brief asks it to return if the format itself must change. Six cases now pass their
focused checks; their patch is intact in its isolated checkout. The remaining two expose an incompatible
wire-format change requiring an unassigned serializer change. Another live lane owns that serializer.
The product decision on compatibility remains with the owner. Project policy allows local checkpoints
after focused checks, and has no requirement to commit a partial assignment.

The delegate must return the six checked cases, their evidence, and the two remaining cases with the
discovered dependency. The lead can continue independent work while resolving compatibility. Neither
the live serializer lane nor the original eight-case obligation may disappear from the account.

## Healthy work without commits

A writer is 38 minutes into a repair with a 60-minute expectation agreed with the lead. Relevant failing
cases declined from 100 to 62 to 25 on unchanged checks at minutes 5, 18, and 34. The completed groups
pass focused checks. It has made 300 tool calls and no commit; the diff is intact in its own checkout.
The remaining cases match the known scope. No other lane is waiting on its result, review remains
feasible, and project policy defers commits until the assignment passes its acceptance checks.

The host provides completion and attention events and bounded waits. The lead has independent work
available and can observe the agreed expectation with those facilities. Nothing here establishes a
stall, lost files, or a reason to weaken checks. A later missed expectation would warrant inspection.

## Shared checkpoints

Two live writers, A and B, have distinct verified worktrees of one repository. They share its stash
stack. A saved checkpoint A1, then B saved checkpoint B1, making B1 the latest entry. Both checkpoints
contain unique uncommitted work; their original base and file lists are recorded. The worktrees are now
clean. A needs its own patch restored for verification, while B still needs B1. No writer has authority
to consume, change, or delete the other's checkpoint.

The immutable identifiers A1 and B1 are verified against each saved patch and base. A stash index is a
position, not an immutable identity. Another push or drop can change it. The engineering decision must
restore A's patch and preserve B's checkpoint, including during cleanup. Serializing shared mutations
or restoring an independently verified immutable checkpoint without stack mutation are available.
Future preservation can use lane-owned state. Worktree paths alone do not isolate the shared resource.

## Delegate brief and a returned problem

The lead is about to dispatch one writer to correct a bookings-screen date label that shows the previous
day for evening bookings west of UTC. The cause is located in one formatting helper, and a focused unit
test plus a screenshot of the screen prove the fix. The writer's isolated checkout at the recorded starting
revision is verified. The host's agent tool accepts a model per dispatch and exposes no effort control;
with no model set, the writer inherits the lead's, the most capable available. A mid-tier model passed
three comparable bounded fixes in this project on the first attempt.

An earlier delegate in this session returned its checked result with one note outside its assignment: the
orders client's retry helper swallows timeouts, so a slow checkout reports success. It attached the failing
request log. Fixing it changes shared client behavior that other services call, and the owner's request
covers only the bookings screen. The project tracks work in GitHub Issues within its authorized workflow.
Nobody has told the owner about the problem yet.

## Proportionate handoffs

These are synthetic return records, not live artifacts. The lead is drafting return instructions for two
independent assignments and deciding how to inspect their results. Both writers have verified isolated
workspaces, bounded authority, and no permission to dispatch other agents. No product choice is open.

A label fix at result S1 has four passing acceptance tests, exit 0, and no findings or blockers. Its whole
result fits a few sentences. A separate cleanup at result L1 has a lengthy implementation report,
producer inventory, raw test logs, and attempt history already retained in accessible project artifacts
`reports/cleanup-L1.md` and `logs/cleanup-L1.txt`. Its acceptance summary is 18 passing tests, exit 0;
one unsupported file type remains a blocker, and a retry defect outside the assignment needs the lead's
disposition. Neither concern is evidence that all cleanup acceptance holds. The original report is
needed by the independent reviewer, not as a copy in the coordinator's conversation. If an evidence
contradiction appears, the lead can inspect the relevant artifact directly.

## Review findings handoff

The independent reviewer has completed a synthetic review of result V1. The following distinct defects
are confirmed, and all need to survive the handoff. Detailed reproductions and failed-check output are
in the accessible existing artifact `reports/review-V1.md`.

| Finding | Location | Trigger and consequence |
| --- | --- | --- |
| F01 | auth/tenant.py:20 | Missing tenant filter exposes another tenant's record. |
| F02 | api/edit.py:44 | An old revision overwrites a newer edit. |
| F03 | jobs/retry.py:31 | A retry duplicates the customer's charge. |
| F04 | storage/remove.py:18 | A missing ownership check deletes another account's file. |
| F05 | export/csv.py:52 | A formula-valued cell executes when the export is opened. |
| F06 | ui/save.ts:90 | A failed save displays success and loses the user's changes. |
| F07 | api/date.py:39 | A missing timezone shifts the accepted business day. |
| F08 | db/migrate.py:77 | Rollback discards records written in the new format. |
| F09 | ops/restore.py:61 | Readiness exposes the service before its data checks finish. |
| F10 | logs/request.py:14 | A credential is written into request logs. |
| F11 | cache/profile.py:29 | A changed permission leaves an authorized cache entry active. |
| F12 | queue/worker.py:48 | An interrupted job is acknowledged before its effect is committed. |

Compatibility on the second supported database is still unverified, not a thirteenth confirmed defect.
The review verdict is blocked. The lead needs every finding's location and consequence, the unresolved
compatibility limitation, and access to the details. A shorter reply that loses F12 is incomplete.
There is no maximum number of findings or requirement to copy the full reproductions into the reply.

## Corrections and stale evidence

The lead previously received a result R1 with an eight-test pass and two unresolved findings, C1 and C2.
The implementer now returns R2. C1 is repaired and a new regression passes; C2 remains a blocker.
The affected nine-test run passes at R2, exit 0, in `logs/R2-checks.txt`, accessible to the lead. An
unaffected format check from R1 remains applicable: its code, dependency, configuration, and environment
inputs are explicitly unchanged. An unrelated integration check has no such equivalence evidence.

A delayed R1 completion claims everything is ready and includes a full copy of the first report.
The accepted current intent is R2 and still includes C2. The lead must not let that delayed completion
replace R2, erase C2, or establish the unverified integration result. A follow-up return can carry the
correction, current identity, updated evidence, and remaining blocker without replaying R1's history.

## Inaccessible and filtered evidence

One writer reports acceptance for result P1 but points only to a report on an inaccessible worker host.
The lead has neither its check output nor another independent acceptance result. The pointer alone
cannot establish acceptance; the writer can provide accessible evidence through the existing private
handoff channel. No new public upload or external service is authorized.

Another result Q1 has a retained terminal record: its acceptance command exited 23 and reported an
ownership-boundary failure. A filter displaying only the last lines exited 0. A summary mistakenly
labels that filter status as the check's status. A separate interrupted Q1 probe has an empty recorded
status and no terminal result. The failed command remains failed, the interrupted probe remains
unverified, and shortening the output must retain both facts. These records authorize read-only
analysis, not rerunning the checks or repairing either result.
