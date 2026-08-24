---
name: github-task
description: Maintain GitHub issue and Project v2 lifecycle after an owning workflow has classified work as tracked. Use for an explicit issue, a selected board item, or a caller-requested tracked unit. Do not decide whether work needs tracking or prescribe how to implement it.
---

# github-task

Act as a GitHub lifecycle adapter. The calling product or technical workflow owns scope, rigor, implementation, verification, and the decision to track work. This skill only keeps an already-tracked unit consistent across the issue, Project v2 board, linked branch, integration, and final board state.

Use the bundled `../../scripts/gh_task_status.py` helper through Python 3. Resolve that path from this file. It keeps large Project v2 payloads out of model context.

## Resolve the lifecycle

1. Run `gh-task-status board` through the bundled helper to resolve the repository, board owner, project number, and default branch. Do not keep mutable board mappings in instructions or memory.
2. If the caller supplied an issue, read it with `gh issue view` and run `gh-task-status show <N>`. If the caller asked for the next tracked item, run `gh-task-status queue` and select only from that output.
3. If the caller explicitly requested a new tracked item, create the issue, attach it to the resolved board, and continue. Set `Human Gate` to `No` only after the owning workflow confirms no protected step is pending. Do not infer that code changes require an issue. Product ideas belong to `idea`; adjacent technical work becomes a separate issue only after the owning workflow classifies it as tracked.
4. Read `Human Gate` before mutation. Only `No` permits a claim. An unset value must be initialized or classified first; another value is a boundary, not a suggestion.
5. Claim the issue with `gh issue develop <N> --repo <owner/repo> --base <base> --name <N>-<slug> --checkout`. Keep the `<N>-` prefix so lifecycle hooks can identify the issue. After the command succeeds and `gh issue develop --list` confirms the linked branch, run `gh-task-status set <N> "In Progress"`.
6. Return control to the owning workflow for implementation and evidence collection. This skill does not select development methods, tests, review depth, or verification cadence.
7. Before integration, require the evidence mandated by the owning workflow and repository policy. Merge or close only through the repository's normal integration path, using `Closes #<N>` when the merge should close the issue.
8. Run `gh-task-status verify <N>` after integration. Repair only the bookkeeping drift it reports, then record the integration commit on the issue.

## Human gates and hierarchy

When work stops at a Human Gate, set `Status` to `Blocked` if that option exists. If the board has no `Blocked` option, preserve its current status. In both cases, comment with the exact dependency and owner, then stop before the protected action.

When one issue gains tracked children, record the parent relationship and use the repository's existing Epic type or label. Work the children, not the parent container.

## Board operations

Use these helper commands instead of broad `gh project` reads:

```text
board [owner/repo]
queue [owner/repo]
show [N|owner/repo#N]
set <N|owner/repo#N> <option>
verify [N|owner/repo#N]
```

Do not use `gh project item-list` or `gh project field-list` for routine lifecycle work because they return large payloads for answers the helper prints on one line. If a lifecycle repair genuinely needs raw Project v2 data, write a narrow GraphQL query for the exact field.

The lifecycle adapter moves a confirmed linked issue to `In Progress`; this is explicit in the skill because host PostToolUse events do not expose shell success consistently enough for a safe remote mutation. GitHub's own `Item closed -> Done` workflow remains the preferred `Done` writer. Write `Done` manually only when `verify` identifies drift.
