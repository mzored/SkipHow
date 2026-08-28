# Delegation

Use this when work will not fit one pass and its parts can advance independently.

Shape the work as a graph, not a list. Establish which parts genuinely block others, then run the ready ones concurrently and reopen the set as each lands. Order alone is not a dependency; a part is blocked only when it needs another's result.

Serialize parts that would change the same shared surface even when nothing else blocks them. Concurrent edits to one file, interface, schema, or migration cost more to reconcile than they save.

Give each delegate a task narrow enough to finish and verify on its own, and point at context rather than copying it. Name the record, the prior change, or the file to read. Repeating context into every brief multiplies cost and lets briefs drift from the source.

A delegate returns its result and evidence. Integrating the work, disposing of findings, and judging completion stay with the root request. Keep integration reviewable: bring each result back and confirm it against the current state rather than trusting a report.

Nothing here requires a branch, worktree, pull request, or review stage. Use those only when the request's authority and the repository's own conventions call for them.

When isolation is warranted, where it lands matters as much as that it exists. Prefer the host's own worktree mechanism, which owns placement and cleanup. Otherwise put the worktree in the location this repository already ignores, and confirm it is ignored before creating anything there rather than assuming. Only when the repository has no such location, use a directory under the temporary area. Never create a worktree beside the repository or anywhere else outside it: a sibling directory is invisible to the project's own ignore rules and cleanup, and it accumulates until someone finds it by accident. Do not edit ignore rules merely to make room for isolation.

Remove what you created once its work is integrated, without forcing. A refusal to remove a worktree or branch is evidence that something still owns it, not an obstacle to override.
