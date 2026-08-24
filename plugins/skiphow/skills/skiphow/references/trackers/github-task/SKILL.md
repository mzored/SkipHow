---
name: github-task
description: Optional GitHub Issues adapter used only after another workflow establishes a need for persistence or tracked lifecycle work.
---

# GitHub adapter

The caller owns scope, priority, implementation, evidence, and the decision to persist. This adapter returns canonical GitHub references and does not choose orchestration or rigor.

Use GitHub automatically only when the repository has a GitHub `origin`, `gh` is authenticated, and no different canonical tracker is configured. Project absence is `NOT_CONFIGURED`, not a failure or degraded core state.

The adapter contract is:

```text
available()
find_duplicate(summary, evidence)
persist(kind, title, body, relationships)
link_delivery(issue, branch_or_pr)
update_optional_view(issue, state)
```

Use native `gh issue create` and `gh issue edit`. Feature-detect issue types, parent and sub-issues, and blocking relationships before using them. Do not invent a label taxonomy or duplicate native relationships in Markdown.

An Issue is the canonical tracked unit. A Project is an optional view or queue. Synchronize one only when explicit configuration identifies it. Never scan all Projects to guess, create a Project during ordinary work, or make Project status a correctness dependency.

Search for a material duplicate before persistence. Use a linked branch or closing pull-request reference only when repository policy or the tracked workflow calls for it. Optional view synchronization may fail independently without blocking completed code.

The bundled scripts are split by responsibility:

- `../../../../../scripts/github_issues.py` for Issue persistence and delivery links.
- `../../../../../scripts/github_project.py` for an explicitly configured optional Project.
- `../../../../../scripts/doctor.py` for read-only availability diagnostics.
