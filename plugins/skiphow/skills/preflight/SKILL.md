---
name: preflight
description: Check SkipHow repository and GitHub readiness without mutation, distinguishing ready, setup-needed, and Issue-only degraded states.
---

# preflight

Use this before tracked development, a first run, or a release when the environment is uncertain. From this skill directory, run the canonical helper with Python 3:

```text
python ../../scripts/gh_task_status.py preflight [owner/repository]
```

The check is read-only. It verifies Python 3.10 or newer, `git`, GitHub CLI 2.93.0 or newer, `gh` authentication, the GitHub repository, shared hooks, and the Codex or Claude plugin command interfaces when those hosts are installed. It also verifies the standard user-facing Project and its minimal `Status` options: `Backlog`, `Ready`, `In progress`, `Waiting`, and `Done`.

Report one GitHub lifecycle state: `READY` when the Project is usable, `SETUP_NEEDED` when standard setup can create or repair it, or `DEGRADED` when permissions or platform capability prevent Project access but Issues remain usable. A missing Project is incomplete recommended setup, not a reason normal engineering must stop.

Report each failure with the helper's concrete repair instruction. Do not create Projects or fields, change options, install tools, authenticate, modify hooks, or mutate Issues or board items. Route requested remediation to `../setup/SKILL.md`. A missing host is reported as skipped, not passed. Use `scripts/verify_release.py --host` for opt-in host smoke checks.
