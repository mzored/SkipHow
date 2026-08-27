# Prior art

SkipHow borrows a small set of ideas from eight projects. It is not a combined version of them, and none is a runtime dependency.

The dated [prior-art research](research/2026-08-25/prior-art.md) records the audited commits, licenses, source findings, test limits, and revalidation triggers. Earlier SkipHow releases distributed selected Matt Pocock skill files with their MIT notices. The current plugin distributes no files from the projects below.

| Project | Keep | Leave out by default |
| --- | --- | --- |
| [GSD](https://github.com/open-gsd/gsd-core) | Fresh context, dependency-aware waves, proportional depth | A large command and workflow tree, mandatory phases, several state files |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec) | One canonical workflow, thin host packaging, delta intent for material contracts | Proposal, specification, design, and task artifacts for every change |
| [Superpowers](https://github.com/obra/superpowers) | Isolated review, bounded repair, concise handoffs, detecting and safely placing Git worktrees | Mandatory brainstorming, approval gates, and test-first development |
| [Matt Pocock skills](https://github.com/mattpocock/skills) | Progressive disclosure, repro-first diagnosis, research before building, triage, findings, and intent-aware conflict resolution | Manual skill chaining and loading the whole library |
| [BMAD](https://github.com/bmad-code-org/bmad-method) | One entry, planning depth based on the work, failure classification | Personas, menus, repeated handoffs, and several ledgers |
| [Paperclip](https://github.com/paperclipai/paperclip) | External task state, idempotent reconciliation, dependency semantics, total outcome cost | A server, task database, company model, and dashboard |
| [Mesa](https://github.com/msoedov/mesa) | Atomic work ownership and event-driven wake-up | An embedded tracker, fixed roles, and company simulation |
| [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin) | Provenance, separation of facts and assumptions, selective dissent | Seventeen standing roles and mandatory scoring |

The shared lesson is concrete. Bounded work stays in one session. Long work keeps a selected queue, dependency-ready waves, bounded ownership, checkpoints, and reconciliation in host and GitHub state. SkipHow adds a new process or artifact only when measured failures show that host-native state cannot support the required outcome.

When future work copies or adapts source text, keep the license, copyright notice, upstream path, and exact commit. When it borrows an idea, describe that idea in SkipHow's own words.
