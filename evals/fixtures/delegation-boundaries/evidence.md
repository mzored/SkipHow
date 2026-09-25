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
