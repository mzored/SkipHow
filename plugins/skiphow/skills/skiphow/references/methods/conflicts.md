# Merge conflict resolution

Use this method only when Git is already in a conflicted merge or rebase. Do not start, abort, reset, or discard an operation unless the request and repository state authorize it.

Recover intent before editing: inspect the merge base, both sides, nearby history, tests, accepted decisions, and the caller behavior each side meant to preserve. Conflict markers show overlapping text, not every semantic conflict, so also check renamed symbols, moved files, changed schemas, ordering, defaults, and tests outside the marked lines.

Resolve the combined intent when both changes are compatible. When they are not, follow the current owner request and accepted product decision; never pick the newer side, the larger side, or the side that compiles most easily by default. Keep unrelated user changes, stage only the resolved paths after inspecting the resulting diff, run focused checks for both intents and then the repository-required integration checks, and report any behavior that could not be preserved or remains `UNVERIFIED`.
