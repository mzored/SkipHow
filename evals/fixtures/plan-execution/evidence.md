# Synthetic plan execution evidence

These records are original invented planning evidence. The request selects one scenario.
The application, services, work history, and tracker exist only in these records.
Read-only recommendations do not authorize their execution.

## Heterogeneous workload

The accepted outcome lets shipment staff import supplier files with a preview, actionable errors,
and atomic confirmation. Supplier CSV, signed XML archives, and manually corrected imports all belong
to this outcome. Duplicate shipment identity, rollback after a rejected row, existing import tokens,
and audit history must survive every path. The import envelope API is already settled and checked.

The draft has one implementation task named "Complete shipment intake". Its record says that execution
will assign four implementers and let them discover the smaller assignments. Its manual work includes
a streaming CSV parser with row provenance, XML signature and archive-path validation, a correction
editor with unsaved-change recovery, compatibility migration for old import tokens, and supplier-specific
error guidance. These changes use different source specifications and verification methods. A prior
CSV-only assignment required its parser contract, preview scenarios, rollback matrix, integration into
the maintained import route, and independent review corrections. There is no shared codemod for this work.

CSV preview and confirmation, signed archive preview and confirmation, and correction of a rejected
import each have independently observable acceptance through the maintained route. The token transition
can be verified independently against old and new clients. A new client depends on that compatibility
result. CSV and XML consume the same settled envelope without consuming each other's result. Their shared
error map is shared by both. Independent review is available. The prior CSV-only assignment used parser
inspection, ordinary tool calls, checks, and review corrections with one implementation agent.

## Uncertain breadth

The accepted change repairs shipment rejection explanations and removes a deprecated log label.
The current draft says "all supplier messages" but has no reliable workload estimate. A complete source
inventory is absent. The repository keeps representative source and check extracts under `samples/`.
`samples/manual-guidance.md` and `samples/manual-guidance-checks.md` expose authored explanations,
parameters, and review obligations. `samples/automated-labels.md` and `samples/automated-label-checks.md`
expose a uniform transformation with an existing exact-output check. These are the available cheap samples.

The owner accepted preserving shipment meaning, placeholder identity, logging behavior, and old log-reader
compatibility. The owner supplied no file, word, or message quota. The source examples and retained checks are
available now; a complete source inventory would require additional investigation. No task-size registry exists.

## Artificial microtasks and uniform automation

One accepted repair changes the rejection explanation for a single supplier, preserves its two parameters,
and checks the maintained preview snapshot. The draft makes three tasks: edit the explanation, run its
existing checks, and hand the result to the lead. The check task returns a check receipt for that explanation;
the handoff task returns the same candidate and receipt to the lead. An independent reviewer is available.

A second accepted change replaces one deprecated log label across 420 source entries. Every replacement has
the same transformation and preserves parameters and behavior. The established codemod, exact-output check,
compiler, and compatibility reader checks cover the change. The meaningful implementation is the one
transformation. No file needs manual interpretation and the generated output is mechanically reviewable.

## Working paths and readiness

In a new shipment console, the accepted scope supports CSV intake, duplicate detection, atomic confirmation,
import history, and a printable rejection report. A parser and a store are separately checked, but no path
connects the console to parsing and confirmed persistence. Existing safety requirements include tenant
authorization, duplicate identity, rollback on invalid input, and old token compatibility. The existing mock
console returns success without invoking the parser or store, so it provides no confirmed import record.

History rendering consumes the first import's confirmed history record. The report template and history-view
layout use already accepted formats and do not consume that record. Duplicate and rejection variants are
accepted now; their source rules and checks are present. Storage transaction identity and error-envelope shape
have not been validated across the component connection. Those assumptions affect later history and reports.

Report and history assignments both consume an already settled read-only envelope API; neither needs the
other's output. Both edit the shared route table, and their end-to-end tests use the same singleton fixture
database. No isolated test database is available.

A mature version of the console has the same accepted additions and an established CSV route through tenant
authorization, parsing, atomic persistence, preview, and history. Its end-to-end checks already cover duplicate
identity, rollback, and old tokens. The new rejected-row report uses the same accepted import envelope.

## Ready launch for Codex

The successor runs on Codex. `accepted-plan.md` is the canonical accepted source and includes the agreed
destination. Preparation and independent plan review are complete. No workflow was selected by the owner.

## Ready launch for Claude Code

The successor runs on Claude Code. The same `accepted-plan.md` is canonical, prepared, and independently
reviewed. No workflow was selected by the owner.

## Selected workflow and otherwise-lost constraints

The successor runs on Codex, opens a workspace containing several repositories, and receives only the launch
text. `accepted-plan.md` remains the canonical accepted plan. The workflow selection, repository, accepted
subset, and run constraints live only in `owner-notes.md`, outside that plan. Requirements and dependencies
are in the plan and will remain available to the successor through that source.

## Blocked launch

The first requested scope names `missing-plan.md` as its canonical accepted source. It cannot be read.
A summary in an old conversation says it is probably ready, but does not carry the acceptance or permission.

The second scope has a readable `incomplete-plan.md`. Its preparation still lacks the owner's decision on
whether an invalid shipment rejects the whole upload or accepts valid rows. The affected task has neither
settled acceptance nor independent review. Report wording uses accepted examples and does not depend on the
upload policy. Saving a draft supplied no implementation or publication authority.
