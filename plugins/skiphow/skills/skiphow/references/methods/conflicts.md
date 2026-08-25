# Merge conflict resolution

Use this method only when Git is already in a conflicted merge or rebase. Do not start, abort, reset, or discard an operation unless the request and repository state authorize it.

## Recover intent

Inspect the merge base, both sides, nearby history, tests, accepted decisions, and the caller behavior each side intended to preserve. Conflict markers show overlapping text, not every semantic conflict. Also inspect renamed symbols, moved files, changed schemas, ordering, defaults, and tests outside the marked lines.

Resolve the combined intent when both changes are compatible. When they are not, follow the current owner request and accepted product decision. Do not silently pick the newer side, the larger side, or the side that makes compilation easiest.

Keep unrelated user changes. Stage only the resolved paths after inspecting the resulting diff. Run focused checks for both intents, then the repository-required integration checks. Report any behavior that could not be preserved and any part of the resolution that remains `UNVERIFIED`.
