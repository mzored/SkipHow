# Intake

Use this reference for `RECORD`. Intake turns raw owner input into useful records; it does not authorize implementation.

## Preserve, split, reconcile

Keep the original wording, who supplied it, when, and any source link. Split mixed input into atomic bugs, ideas, questions, risks, or observations. Inspect enough project and tracker context to make each record actionable, mark unsupported conclusions as assumptions, and give each record a type and a proposed priority with its reason (user impact, risk, cost), so the owner reorders a batch instead of writing tickets.

Search the tracker for the same behavior and outcome before creating anything; similar wording alone is not a duplicate. Give each signal one disposition: `NEW`, `UPDATE` (adds evidence or scope to an existing item), `DUPLICATE` (links and explains the match), `RELATED` (separate work with shared context), `NEEDS_RESEARCH` (a material unknown), or `DISMISSED` (evidence shows it false or obsolete). Merge signals only when they share the outcome and the acceptance evidence.

Never copy secrets, customer data, private paths, or vulnerability details into a public tracker; return a redacted finding instead.

## Save once

With GitHub connected and persistence granted, create or update Issues, preserve earlier owner text, and add evidence in comments or append-only sections. Read [GitHub](github.md) for markers and batch labels.

Without GitHub, append one block per signal to `.skiphow/inbox.md`. Do not create a second ledger.

```text
## <stable-id>
- Recorded: <output of `date -u +%Y-%m-%dT%H:%M:%SZ`, or `unknown` when no clock is available>
- Source: <person, request, file, or URL>
- Original: <source wording when it fits on one line>
- Normalized: <actionable work item>
- Disposition: <NEW | UPDATE | DUPLICATE | RELATED | NEEDS_RESEARCH | DISMISSED>
- Priority: <proposed priority and its reason>
- Links: <canonical IDs or None>
- Evidence: <known evidence or None>
- Assumptions: <unsupported conclusions or None>
- Open questions: <material unknowns or None>
```

For multiline source text, replace `Original` with `Original JSON` holding one JSON-escaped string. Correct an older record with a new linked block, not by rewriting it.

Report disposition counts, the canonical links, the batch marker, and the proposed order. Mention only decisions or missing information that changes what should be saved.
