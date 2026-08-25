---
name: resolving-merge-conflicts
description: Internal capability for resolving an already in-progress Git merge or rebase conflict by recovering both sides' intent and verifying the integrated result.
---

# Resolving merge conflicts

Use this capability only when Git is already in a conflicted merge or rebase state. Do not begin a merge or rebase merely to invoke it, and do not abort, reset, or discard either side unless the user has explicitly authorized that destructive outcome.

1. Inspect the exact Git state, operation, commits, unmerged paths, conflict stages, and repository instructions.
2. Recover why each side changed. Use commits, issues, pull requests, tests, accepted specifications, and surrounding code as primary evidence. Treat conflict markers as symptoms, not intent.
3. Resolve each hunk to preserve both compatible intents. When they are incompatible, choose the result required by the stated integration goal and governing product or technical authority. Do not invent unrelated behavior. Escalate only a genuine unresolved product choice or protected action.
4. Check for semantic conflicts outside marked hunks: renamed call sites, schema or API drift, duplicated behavior, and tests that encode only one side.
5. Run the smallest relevant checks, then every repository-required final gate. Fix failures caused by the integration without absorbing unrelated work.
6. Stage only the resolved operation's files and continue the merge or rebase through all remaining commits. Report the final Git state, preserved intent, checks, and any residual uncertainty.
