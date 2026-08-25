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
find_candidates(summary, evidence?)
find_duplicate(summary)
persist(kind, title, body, relationships)
create_linked_branch(issue, name)
record_delivery(issue, url)
update_optional_view(issue, state, status_field, status_mapping)
```

Candidate search is bounded; the caller makes semantic duplicate decisions. `find_duplicate` returns only an exact normalized title. Use native `gh issue create`. Feature-detect issue types, parent and sub-issues, and blocking relationships before using them. Do not invent a label taxonomy or duplicate native relationships in Markdown.

An Issue is the canonical tracked unit. A Project is an optional view or queue. Synchronize one only when explicit configuration identifies it. Never scan all Projects to guess, create a Project during ordinary work, or make Project status a correctness dependency.

Search for a material duplicate before persistence. Branch creation is an explicit remote mutation through `create_linked_branch`. `record_delivery` adds provenance only; it is not a native PR link or closing relation. Put `Closes #N` in a pull request when native close semantics are needed. Optional view synchronization needs an explicit field and option mapping and may return `UNVERIFIED` without blocking completed Issue or delivery work.

The bundled scripts are split by responsibility:

- `../../../../../scripts/github_issues.py` for Issue persistence and delivery links.
- `../../../../../scripts/github_project.py` for an explicitly configured optional Project.
- `../../../../../scripts/doctor.py` for read-only availability diagnostics.
