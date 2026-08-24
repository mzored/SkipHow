---
name: github-task
description: Maintain native GitHub Issue lifecycle and the default Project work surface after an owning workflow classifies work as tracked. This adapter does not decide scope or implementation.
---

# github-task

Act as a thin GitHub lifecycle adapter. The calling product or technical workflow owns scope, priority, rigor, implementation, verification, and the decision to persist work. This skill translates that established intent into native GitHub state and returns a canonical issue or pull-request reference.

When the repository `origin` is GitHub and `gh` is authenticated, use GitHub automatically. Do not ask the user to choose a tracker or explain GitHub mechanics. If the environment already identifies a different canonical tracker, return control to that adapter instead of creating a parallel GitHub backlog.

## Resolve the tracked unit

1. Resolve the repository, default branch, authentication, and any explicit issue or pull request from primary GitHub state. Read the issue body and relevant comments.
2. If the caller asks for an existing or next tracked unit, use the configured Project as the default queue. In `DEGRADED` mode, inspect open Issues and their native dependencies; do not invent priority from labels.
3. Before persistence, search for a materially equivalent open Issue. Link a duplicate rather than creating another unit.
4. Create a minimal Issue only when the caller has already requested tracking or classified a finding `PERSISTED`. Use native `Bug`, `Feature`, or `Task` type when that type is available. Use native parent/sub-issue and blocking relationships through current `gh issue create` or `gh issue edit` flags. Keep dependency edges out of duplicated Markdown when GitHub already stores them.

Do not create a default label taxonomy. Add a label only for semantic information not represented by issue type, hierarchy, dependencies, state, assignee, milestone, or an existing configured Project. Do not install Issue Forms during runtime; they are an optional repository setup for meaningful external reporting.

## Carry the lifecycle

For implementation, create or reuse a linked branch with `gh issue develop` when that is the repository's normal path. Keep the issue number in a generated branch name only when needed by the host lifecycle hooks. Return control to the owning workflow for implementation, evidence, review, and integration.

Use `Closes #<N>` in the pull request when merge should close the issue. After integration, verify the issue, linked pull request, and delivered commit from GitHub. Repair only lifecycle drift authorized by the caller, then record the integration reference on the issue when useful.

The Project is the standard user-facing queue and status view, while the Issue remains the canonical work object. Use the bundled `../../scripts/gh_task_status.py` helper for compact `board`, `queue`, `show`, `set`, and `verify` operations when the configured Project is available. Prefer its built-in automation for adding Issues and completing merged work. Absence or temporary failure of the Project is a setup deficiency, not a correctness dependency: continue in Issue-only `DEGRADED` mode and direct explicit setup or repair requests to `../setup/SKILL.md`.

Never create or redesign a Project during ordinary task lifecycle. The standard Project has only a small Status workflow (`Backlog`, `Ready`, `In progress`, `Waiting`, `Done`) and saved human views. Do not require `Human Gate` or any private SkipHow schema.

When work reaches a human-only or protected action, follow the owning CTO human-action handoff. Record the exact dependency and owner on the Issue; synchronize an existing Project's blocked state only when it already has a compatible option. Do not encode scope, risk, testing, diagnosis, review policy, product decisions, or orchestration in labels or Project fields.
