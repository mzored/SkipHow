---
name: idea
description: Internal capture workflow that saves exactly one requested idea without shaping or implementing it.
---

# Capture

The explicit request to save or record an idea authorizes one persistence action. Do not research, expand, prioritize, shape, or implement it.

1. Use the canonical tracker named by repository instructions or configuration.
2. Otherwise, when `origin` is GitHub and authenticated `gh` is available, use a GitHub Issue without requiring a Project.
3. Otherwise, use `.skiphow/inbox.md` as the canonical local fallback. Do not create it when the repository defines another tracker or the user did not request persistence.
4. Search the chosen store for a material duplicate before adding an item.

For the local fallback, create the parent directory only when the first item is saved. Use a short human-readable entry:

```text
## SKH-YYYYMMDD-NN: concise title

Captured: YYYY-MM-DD
Source: user request

<The user's idea, edited only enough to stand alone.>
```

Preserve each local ID and `Source` when migrating to GitHub later. Return the issue link or local ID and stop.
