# Prior art

SkipHow was informed by the projects below. It is not a superset of them. Except for the pinned Matt Pocock reference files described under [Vendored source](#vendored-source), these projects are research inputs, not copied code or runtime dependencies.

## Adopted and rejected ideas

| Project | Ideas adopted | Ideas rejected as defaults |
| --- | --- | --- |
| [GSD](https://github.com/open-gsd/gsd-core) | Durable context for long work, fresh sessions for independent work, model selection as configuration | A required discuss, plan, execute, verify, and ship sequence for every change |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | Intent and delta traceability for material, long-running work | A proposal, specification, design, and task directory for every change |
| [Superpowers](https://github.com/obra/superpowers) | Failure-corpus testing, worktree and review techniques, scoped re-review | Mandatory brainstorming, approval gates, and strict test-first development |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | Progressive disclosure, context-load discipline, and remediation references | Loading a general engineering-method library into every request |
| [BMAD](https://github.com/bmad-code-org/bmad-method) | Depth proportional to the work and a durable epic loop | Personas, handoffs, and required briefs or specifications |
| [Paperclip](https://github.com/paperclipai/paperclip) | Separation of control and execution, budgets, audit records, and adapters | An organization chart, governance UI, and always-on server as defaults |
| [Mesa](https://github.com/msoedov/mesa) | Local-first operation, single-binary simplicity, and embedded durable state | Fixed roles and company simulation |
| [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin) | Batch signal intake, evidence provenance, and disconfirming evidence | A fixed 17-agent topology and mandatory formal scoring |
| [Restate](https://docs.restate.dev/ai-quickstart) and [Temporal](https://docs.temporal.io/production-deployment) | Candidates for durable execution, retries, waits, and recovery, subject to an executable spike | Adopting an operational platform before measured recovery needs justify it |

These choices keep the common path outcome-first. Process, persistence, and orchestration are added only when the work needs them.

## Vendored source

The repository currently vendors selected reference files only from [mattpocock/skills](https://github.com/mattpocock/skills). All copies use commit [`6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`](https://github.com/mattpocock/skills/tree/6654f6b60cd9d5be8b54c6fafe44346dabeb3b76) and the upstream MIT license, copyright Matt Pocock, 2026.

The vendored groups are:

- prototype;
- resolving merge conflicts;
- diagnosing bugs;
- testing;
- technical review;
- codebase design.

Each `upstream/` directory contains the copied license. Its adjacent `SOURCE.md` records the upstream paths. The canonical [source manifest](../plugins/skiphow/skills/skiphow/references/third_party/sources.json) records the full commit pin, provenance, review date, local and upstream paths, and SHA-256 digest for every copied file. The parent SkipHow files are adaptations and remain authoritative for invocation, authority, and delivery policy.

Do not update a vendored file without updating its pin or digest in the manifest and retaining the applicable license and source notice. A repository link in the table above is not a source pin and does not authorize copying.
