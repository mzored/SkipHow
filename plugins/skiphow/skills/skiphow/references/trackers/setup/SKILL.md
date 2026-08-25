---
name: setup
description: Internal explicit setup workflow for optional SkipHow tracker configuration or a user-requested GitHub Project.
---

# Optional integration setup

Use this only when the user explicitly asks to configure, repair, enable, or create an integration. Core SkipHow needs no setup, Python, `gh`, authentication, Issue, Project, or hooks.

Start with a read-only inspection and show the intended changes. Keep setup idempotent. Offer a dry run before remote mutation when the command supports it.

If the user asks for GitHub tracking, prefer Issues. If the user asks for a Project or board, create or connect one explicit Project and store its owner and number in optional configuration. Do not scan the user's Projects to choose one. Preserve unrelated fields and views. Do not create labels or a universal status schema unless the user asks for those exact fields.

Write `.skiphow/config.json` only when the user explicitly requests configuration:

```json
{
  "schema_version": 2,
  "tracker": {"type": "auto", "project": null},
  "delivery": {"merge_policy": "never", "cleanup": "merged_only"},
  "findings": {"persist": "local"},
  "campaign_root": ".skiphow/runs"
}
```

Accepted tracker types are `auto`, `none`, `github`, and `local`. `project` is `null` or an explicit `owner/number`. Merge defaults to `never`; cleanup defaults to merged, system-owned resources only. Finding persistence is `local`, `tracker`, `ask`, or `off`. `campaign_root` must be a relative path inside the project. Reject unknown keys, absolute paths, and traversal. The file is never required.

Read v1 configuration without mutation. Migrate only during explicit setup or update. Write an adjacent backup before replacing v1, then validate the v2 result. Provider credentials and model IDs belong in provider stores or personal configuration, never this project file.
