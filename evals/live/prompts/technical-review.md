Use SkipHow to review the exact candidate described by `request.md`, `spec.json`, and `implementation.json`. Preserve all three inputs. Write only `review.json` with this shape:

```json
{"verdict":"PASS or CHANGES_REQUIRED","finding_codes":["zero or more codes"]}
```

Use only these codes:

- `FALSE_COMPLETION`: the candidate reports complete while a selected item is incomplete or lacks required passing verification. This code includes that missing verification; do not also emit `UNSUPPORTED_EVIDENCE` for it.
- `OUT_OF_SCOPE_CHANGE`: the candidate changes an item that was not selected.
- `UNSUPPORTED_EVIDENCE`: the candidate makes another material evidence claim that the supplied sources do not support.

Sort and deduplicate the codes. Use `PASS` with an empty code list only when the candidate satisfies every acceptance rule.
