# Intake

Use this reference for `RECORD`. Intake turns raw owner input into useful records. It does not authorize implementation.

## Preserve the source

Keep the original text, who supplied it, when it arrived, and any source link. Split a mixed request into atomic signals without erasing the original wording. A signal may be a bug, idea, question, request, risk, or observation.

Inspect enough project and tracker context to make each record actionable. Do not invent certainty. Mark unsupported conclusions as assumptions.

## Reconcile before creating

Search the canonical tracker for the same behavior, outcome, and evidence. Similar wording alone does not prove a duplicate.

Give each signal one disposition:

- `NEW` creates a work item.
- `UPDATE` adds evidence or scope to the same work item.
- `DUPLICATE` links to an equivalent work item and explains the match.
- `RELATED` links separate work that shares context or dependencies.
- `NEEDS_RESEARCH` records a material unknown without pretending it is ready to build.

Merge signals only when they describe the same desired outcome and acceptance evidence. Keep separate priorities or independent release paths separate.

## Save once

Use GitHub Issues when the project connects GitHub and the owner authorized persistence. Follow `github.md` for remote records.

Without GitHub, append records to `.skiphow/inbox.md`. Use stable identifiers and include source, normalized work item, disposition, links, evidence, and open questions. Do not create a second JSON ledger or task database.

Return a compact count of signals, work items, duplicates, related items, and items needing research. Mention only decisions or missing information that changes what should be saved.
