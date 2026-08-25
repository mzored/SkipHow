# Intake

Use this reference for `RECORD`. Intake turns raw owner input into useful records. It does not authorize implementation.

## Preserve the source

Keep the original text, who supplied it, when it arrived, and any source link. Split a mixed request into atomic signals without erasing the original wording. A signal may be a bug, idea, question, request, risk, or observation.

Inspect enough project and tracker context to make each record actionable. Do not invent certainty. Mark unsupported conclusions as assumptions.

Do not copy secrets, customer data, private paths, or vulnerability details into a public tracker. Redact the record without losing the actionable fact. Send a security finding only through an authorized private channel. If none exists, return a redacted ready-to-save record.

## Reconcile before creating

Search the canonical tracker for the same behavior, outcome, and evidence. Similar wording alone does not prove a duplicate.

Give each signal one disposition:

- `NEW` creates a work item.
- `UPDATE` adds evidence or scope to the same work item.
- `DUPLICATE` links to an equivalent work item and explains the match.
- `RELATED` links separate work that shares context or dependencies.
- `NEEDS_RESEARCH` records a material unknown without pretending it is ready to build.
- `DISMISSED` preserves a signal that evidence shows is false or obsolete.

Merge signals only when they describe the same desired outcome and acceptance evidence. Keep separate priorities or independent release paths separate.

## Save once

Use GitHub Issues when the project connects GitHub and the owner authorized persistence. Follow [GitHub delivery](github.md) for remote records. Preserve earlier owner text and provenance. Add new evidence in a comment or an append-only marked section instead of rewriting the prior record.

Without GitHub, append records to `.skiphow/inbox.md`. Use stable identifiers and include source, normalized work item, disposition, links, evidence, and open questions. Do not create a second JSON ledger or task database.

Use one append-only Markdown block per signal so another session can reconstruct it without a private schema:

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

For multiline source text, replace `Original` with `Original JSON` and store one JSON-escaped string. Use exactly one of those fields. A new record includes `Assumptions`; older records without it remain readable. Do not rewrite earlier blocks. Use `DISMISSED` only when evidence shows that a captured finding is false or no longer relevant, and preserve the reason in `Evidence`.

Return a compact count of every disposition and include canonical links for saved records. Mention only decisions or missing information that changes what should be saved.
