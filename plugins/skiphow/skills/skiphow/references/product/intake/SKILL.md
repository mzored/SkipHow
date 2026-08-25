---
name: intake
description: Internal workflow for capturing, classifying, deduplicating, and persisting one or more product signals.
---

# Product intake

Intake accepts ideas, bugs, requests, feedback, risks, questions, and mixed batches. Preserve the source meaning and provenance. Do not implement, prioritize the roadmap, or turn uncertain reports into confirmed defects.

## Single-item fast path

For `CAPTURE`, create one concise standalone record. Do not research or shape it. Search the chosen store for a semantic duplicate, then link or update the canonical record when appropriate. Otherwise create one item and return its identity.

## Batch intake

1. Split input into atomic signals without losing source grouping or wording needed for context.
2. Classify each signal as idea, bug report, feature request, feedback, risk, question, or another project-defined type. Classification is not validation.
3. Preserve provenance: source, capture date, supplied links or evidence, and relationships between signals.
4. Search the canonical store for semantically related candidates. Compare behavior, affected user, conditions, and desired outcome rather than title equality. The controller decides `DUPLICATE`, `UPDATE`, `CREATE`, or `NEEDS_RESEARCH`; the adapter only returns candidates and performs the selected operation.
5. Add a short recommendation when the request asks for triage: next action and reason, with uncertainty stated. Do not invent priority, severity, confidence, or evidence.
6. Persist only when the user requested capture or repository policy requires it. Preview or analysis requests stay read-only.

## Persistence

Use the repository's canonical tracker. Otherwise, when configured GitHub access is available, use Issues without requiring a Project. If neither applies, use `.skiphow/inbox.md`. Create the local file only for authorized persistence.

Use native parent, subissue, duplicate, and blocking relationships when the adapter detects support. If a relationship is unavailable, preserve it as a plain linked reference and report that native mapping as `UNVERIFIED`; do not emulate a hidden workflow with labels.

For the local fallback, preserve stable IDs and provenance so records can migrate later:

```text
## SKH-YYYYMMDD-NN: concise title

Captured: YYYY-MM-DD
Source: user request
Type: idea | bug report | feature request | feedback | risk | question
Related: optional stable IDs

<Signal edited only enough to stand alone.>
```

On later migration, keep the local ID and source in the destination record. Return created, updated, duplicate, and unresolved items with canonical links or IDs.
