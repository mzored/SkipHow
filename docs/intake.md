# Product intake

Product intake turns one or many raw product signals into a small set of useful records. A signal may be a bug report, idea, question, risk, maintenance concern, or customer feedback. A signal is evidence for work, not automatically a work item.

## Contract

Intake preserves each raw record and each atom's source, verbatim text, context, observed evidence, confidence, timestamp, and links. It may inspect the product or repository when that changes the disposition. It then:

1. separates distinct signals without losing provenance;
2. classifies them as `BUG`, `IDEA`, `QUESTION`, `RISK`, `TECH_DEBT`, or `FEEDBACK`;
3. groups related signals and searches a bounded set of candidate duplicates;
4. distinguishes observations from speculation;
5. recommends `NOW`, `NEXT`, `LATER`, `DECLINE`, or `INVESTIGATE`;
6. persists records only when the request, existing tracked work, or repository policy authorizes it.

Candidate search is lexical and bounded to twenty results. The controller records one of `CREATE`, `UPDATE`, `DUPLICATE`, `RELATED`, `DISTINCT`, or `NEEDS_RESEARCH` with a reason. Similarity alone never merges records. A confident duplicate adds provenance to the existing item. Partial overlap remains related or distinct.

Only actionable work becomes an Issue or task. Several signals may support one work item. A large list becomes an Epic only when it describes one outcome with several independently deliverable items and real dependencies.

A work item contains the problem or outcome, why it matters, acceptance, non-goals, evidence and provenance, and relationships or dependencies. Intake does not invent a PRD, architecture, file list, or implementation plan.

GitHub is optional. Native issue types and relationships are used only when available and configured. They do not require a custom label taxonomy. Direct plugin capture can fall back to `.skiphow/inbox.md`. The Python Intake module has a separate structured ledger at `.skiphow/intake/signals.jsonl` and `.skiphow/intake/work-items.json`.

## Authority and result

Intake never changes portfolio priority on its own. It does not implement captured work unless the user also authorized implementation. The result is one owner-facing summary of created, updated, deduplicated, declined, and unresolved records, with canonical references for persisted items.

## Current implementation status

The plugin routes both `INTAKE` and the single-item `CAPTURE` fast path. The Python module accepts strings, mappings, explicit lists, and line-separated notes. It retains raw-record identity when it atomizes a record, marks unsupported bug claims as speculative risks, groups related signals without dropping provenance, shapes only actionable groups into work items, and validates Epic parent and dependency graphs. Exact local replay is a no-op, while an identity collision with different content fails.

The CLI currently atomizes and optionally persists signals. Grouping, work-item shaping, candidate decisions, and Epic mapping are Python APIs used by the product controller; the CLI does not run that full sequence automatically. The GitHub helper supports bounded candidates, keyed provenance, updates, and native relationship reconciliation with a fallback. Deterministic tests cover mixed batches, atom provenance, grouping, decision validation, Epic graphs, collision handling, and local replay. Live model judgment remains `UNVERIFIED`.
