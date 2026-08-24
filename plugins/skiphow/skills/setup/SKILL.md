---
name: setup
description: Configure the standard SkipHow GitHub work surface for a repository by reusing or bootstrapping a minimal Project while preserving Issue-only degraded operation.
---

# setup

Use this owner-facing workflow when the user asks to install, configure, repair, or complete SkipHow's GitHub setup. It may create or modify a GitHub Project only within that explicit setup request. Read `../preflight/SKILL.md`, inspect the repository and GitHub state, and use current official GitHub CLI and API behavior.

GitHub Issues are the durable work identities. The Project is the default human-facing queue and status surface. Reuse one existing compatible Project linked to the repository. If none exists and the authenticated account has `project` scope, bootstrap one minimal Project, link it to the repository, and configure only:

- a `Status` field with `Backlog`, `Ready`, `In progress`, `Waiting`, and `Done`;
- a board grouped by Status;
- an Active view excluding `Done`;
- a Needs attention view filtered to `Waiting`.

Prefer GitHub built-in automation for adding repository Issues and moving closed Issues or merged pull requests to `Done`. Preserve compatible existing automation. If current supported APIs cannot configure a view or workflow, use the CTO human-action handoff with the exact GitHub page and clicks, then verify the result; do not invent an undocumented mutation.

Do not create `Human Gate`, risk, complexity, agent, execution, review, validation, or root-cause fields. Do not create a label taxonomy or organization Issue fields. Preserve unrelated existing fields and views. Issue Forms remain an explicit optional setup only for repositories with meaningful external reporters.

Finish in exactly one state:

- `READY`: the Project is linked and its minimal status surface is usable;
- `SETUP_NEEDED`: configuration is incomplete but can be completed with available authority or one stated human action;
- `DEGRADED`: Project access is unavailable because of permissions or platform capability, while native Issues remain usable.

Never block ordinary engineering in `DEGRADED` when Issues are available. Report the Project URL when ready, every change made, any built-in automation verified, and the exact remaining action otherwise.
