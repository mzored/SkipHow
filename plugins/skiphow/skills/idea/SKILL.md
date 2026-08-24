---
name: idea
description: Capture a raw product idea in the project's canonical tracker without researching, shaping, prioritizing, or implementing it.
---

# idea

Capture only. The request to save or record the idea authorizes creating one item in the project's canonical tracker.

1. Find the canonical tracker from repository instructions and current project configuration. In a GitHub-backed project, use a GitHub issue unless the repository names another tracker.
2. Reuse an existing matching item instead of creating a duplicate.
3. Write a concise title and preserve the Owner's wording in the body:

   ```text
   Raw idea:
   <the Owner's words, edited only enough to stand alone>

   Context:
   <context already present in the request, or "Not provided">

   Captured:
   <current date>
   ```

4. Apply the tracker's existing `idea` state or label. Do not invent a parallel backlog file.
5. Return the item link or identifier and stop.

Do not research competitors, assess feasibility, set priority, write a product contract, or start implementation. If no canonical tracker is available, report the missing capture destination instead of creating `ideas.md`, JSON, or another local source of truth.
