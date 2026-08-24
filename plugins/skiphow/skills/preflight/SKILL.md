---
name: preflight
description: Check a SkipHow repository and its adopted GitHub lifecycle before delivery. It reports fixes and never changes local or remote state.
---

# preflight

Use this before tracked development, a first run, or a release when the environment is uncertain. From this skill directory, run the canonical helper with Python 3:

```text
python ../../scripts/gh_task_status.py preflight [owner/repository]
```

The check is read-only. It verifies Python 3.10 or newer, `git`, GitHub CLI 2.93.0 or newer, `gh` authentication, the repository, the adopted Project v2 lifecycle schema, shared hooks, and the Codex or Claude plugin command interfaces when those hosts are installed. It expects these single-select fields and options:

- `Status`: `Todo`, `In Progress`, `Done`, `Blocked`
- `Human Gate`: `No`, `Deploy`, `Product decision`, `External`

Report each failure with the helper's concrete repair instruction. Do not create fields, change options, install tools, authenticate, modify hooks, or mutate board items. A missing host is reported as skipped, not passed. Use `scripts/verify_release.py --host` for opt-in host smoke checks.
