# Intake

Use this reference for `RECORD`. Intake turns raw owner input into useful records. It does not authorize implementation.

## Preserve the source

Keep the original text, who supplied it, when it arrived, and any source link. Split mixed input into atomic bugs, ideas, questions, risks, or observations without erasing the original wording. Inspect enough project and tracker context to make each record useful. Mark unsupported conclusions as assumptions.

Do not copy secrets, customer data, private paths, or vulnerability details into a public tracker. A security channel is valid only when the owner selected it or an authenticated security feature matches the active repository. Otherwise return a redacted ready-to-save finding.

## Reconcile before creating

Search the canonical tracker for the same behavior, outcome, and evidence. Similar wording alone does not prove a duplicate.

Give each signal one disposition:

- `NEW` creates a work item.
- `UPDATE` adds evidence or scope to the same work item.
- `DUPLICATE` links to an equivalent item and explains the match.
- `RELATED` links separate work with shared context or dependencies.
- `NEEDS_RESEARCH` records a material unknown.
- `DISMISSED` preserves a signal that evidence shows is false or obsolete.

Merge signals only when they share the desired outcome and acceptance evidence. Keep separate priorities and release paths separate.

## Save once

Use GitHub Issues when the project connects GitHub and the owner authorized persistence. Preserve earlier owner text and provenance. Add evidence in a comment or append-only marked section.

Without GitHub, append records to `.skiphow/inbox.md`. Do not create a second JSON ledger or task database. Use one block per signal:

```text
## <stable-id>
- Recorded: <RFC 3339 UTC timestamp>
- Source: <person, request, file, or URL>
- Original: <source wording when it fits on one line>
- Normalized: <actionable work item>
- Disposition: <NEW | UPDATE | DUPLICATE | RELATED | NEEDS_RESEARCH | DISMISSED>
- Links: <canonical IDs or None>
- Evidence: <known evidence or None>
- Assumptions: <unsupported conclusions or None>
- Open questions: <material unknowns or None>
```

For multiline source text, replace `Original` with `Original JSON` and store one JSON-escaped string. Use exactly one of those fields. Correct an older record with a new linked block instead of rewriting it.

Return compact disposition counts and canonical links. Mention only decisions or missing information that changes what should be saved.
