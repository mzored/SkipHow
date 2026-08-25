# Verified project context

Maintain project context only through an explicit request:

- `setup`: create one small verified block in the existing `AGENTS.md` or canonical repository instruction file;
- `refresh`: reverify existing entries and update their evidence or date;
- `record`: add a recurring mistake or non-obvious constraint that is expensive to rediscover;
- `audit`: remove stale, duplicated, obvious, or unsupported entries.

Do not infer or update context automatically. Preserve the repository's existing instruction structure and mutation rules.

Store only governance rules, protected areas, unusual runtime cost, and repeated agent mistakes that source inspection does not reveal cheaply. Do not copy the stack, file layout, ordinary commands, or other facts that the project exposes directly.

Each entry names its source or evidence and the date it was last verified. If evidence is unavailable, omit the entry or mark the uncertain claim for human review. An audit removes stale rules instead of accumulating historical advice.
