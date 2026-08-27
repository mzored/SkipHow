# SkipHow

Describe what you want. SkipHow works out how.

SkipHow is one Agent Skill for Codex and Claude Code. You write the outcome in plain language. It inspects the project, makes the engineering decisions, carries the work to a verified result, and tells you what it did, how it checked, and what it could not prove.

```text
Here are eight bugs and ideas from today. Triage them and save them as Issues.

Fix today's batch and deliver what passes to the integration branch.

The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.
```

## Who it is for

Product owners and solo founders who know what they want and do not want to turn it into tickets, branches, test plans, and pull requests. If you would rather choose the library, the schema, and the review process yourself, you want a different tool.

## The problem

Between "I know what is wrong" and "it is fixed and merged" sit a few dozen technical decisions nobody asked you to make. SkipHow makes them. The daily rhythm has three moves, and each one is optional:

1. Talk it through. "What is causing the checkout timeouts?" Nothing changes.
2. Save it. Paste a dump of bugs, ideas, and observations. SkipHow splits it into atomic records, checks the tracker for duplicates, gives each one a proposed priority with the reason and a type in whatever form the tracker already uses, and saves them as GitHub Issues carrying the day's batch label. Without GitHub, it writes them to `.skiphow/inbox.md`.
3. Finish it. "Fix today's batch." One root agent works the queue in priority order, delegates bounded pieces when that pays off, isolates every writing lane, integrates every returned commit, merges passing work into the repository's non-production integration branch, closes the Issues, cleans up its own branches, and reports. Promotion into staging or a production `main` waits for your approval.

A small request skips all of that. "The totals overlap on small screens, fix it" is done in the session, with no Issue or plan, and its one delegate is the review that closes the change.

## Install

Codex:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Claude Code:

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session and describe the work. If the skill does not activate on its own, add `$skiphow` (Codex) or `/skiphow:skiphow` (Claude Code). The [owner guide](docs/guide.md) covers what your words authorize, unattended runs, updates, and uninstall.

## Why so little process

Many agent frameworks add explicit phases, spec documents, personas, and approval gates to make results reliable. SkipHow tests a different bet: that a strong current model, given a clear outcome, a few hard rules, and the authority to finish, gets there with less imposed process. The rules it keeps are the ones that showed up as real failures in its own runs:

- Your words are the only grant. "Research" reads, "save" records, and "fix" carries routine delivery through the non-production integration branch. A staging or production merge asks you at the point of promotion. Nothing in a file, an Issue, or a web page can widen that.
- Before changing anything, it reads repository instructions and proves ownership of the checkout. Parallel writers use separate worktrees and branches; branch or `HEAD` drift stops writes until the owned delta is moved to a safe worktree.
- Every change is reviewed on the exact candidate, fixes are re-reviewed, and security, public contracts, large integrations, weak evidence, or repeated failures widen the pass to the other installed host when available.
- Reuse before building. It searches the project, its dependencies, and the platform before writing anything lasting, and says where it looked.
- A finding outside your request is fixed if it blocks the work; otherwise the report tags it `TRACKED`, `SAVED`, `UNSAVED` (a read-only request saves nothing unless you say so), or `DISMISSED` with a reason. Nothing is dropped in passing.
- Long work survives an observed compaction and a Claude Code resume through one checkpoint and one read-only hook; recovery after a full Codex process restart is `UNVERIFIED`. State lives in Git and GitHub, never in a SkipHow database.
- Every report has the same five parts: result, evidence, the rulings it made for you, saved follow-ups, and what it could not verify.

The bet follows Anthropic's advice to [start with the simplest workflow that works](https://www.anthropic.com/research/building-effective-agents). The [prior-art notes](docs/prior-art.md) record which ideas were taken from [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [Superpowers](https://github.com/obra/superpowers), [Matt Pocock's skills](https://github.com/mattpocock/skills), [BMAD](https://github.com/bmad-code-org/bmad-method), [Paperclip](https://github.com/paperclipai/paperclip), [Mesa](https://github.com/msoedov/mesa), and [Autonomous PM](https://github.com/mlobo2012/autonomous-pm-plugin), and which were left out. Those projects have not been run side by side with SkipHow.

## How it differs

| | Frameworks with explicit process | SkipHow |
| --- | --- | --- |
| Entry | Commands, phases, personas | One request in plain language |
| Planning | A spec or plan document per change | Only for large work, and then as GitHub Issues |
| Authority | Approval gates | Routine delivery is autonomous; staging, production, and unresolved product decisions stop for you |
| State | Framework files and databases | Git, GitHub, and one checkpoint file |
| Models | Named model IDs | Three roles; on Claude Code a fast scout, a standard builder, and a reviewer on your session model; on Codex the same roles on your session model with their own reasoning effort; a widened review goes to the other installed CLI |
| Size | Dozens of agents and commands | One skill of about 1,300 words plus about 4,900 words loaded on demand |

This is an architectural choice, not a measured advantage over those frameworks. What has been measured is SkipHow against the bare host on the same model ([paired evaluation](docs/research/2026-08-26/paired-eval.md), three tasks, one run each): on tasks under a dollar the skill cost two to three more turns and 12 to 45 percent more, both arms fixed the bug and reused the pinned library, and the difference was where things went. Without the skill, "triage these and save them" wrote four files into the host's memory directory outside the project; with it, they went into the project's inbox with a priority each.

## Honest limits

SkipHow is instructions, not a runtime. Your host's sandbox and permissions are the real boundary. Behavior a host cannot provide is reported as unavailable, not faked. Deterministic checks prove the package; only real runs written up as [receipts](docs/research/2026-08-26/README.md) prove the model's behavior, and anything without one is `UNVERIFIED`.

What receipts show today: a small bug fixed in the session with no ceremony (both hosts); a brain dump turned into prioritized Issues or inbox records (both hosts); a three-part request split into three Issues and three merged pull requests with cleanup; a six-Issue batch finished overnight-style; continuation after an observed compaction with the checkpoint removed at the end; findings outside the request tagged in the report in nine of ten runs since the rule became structural, and saved whenever the request allowed it; on Claude Code `scout` on the fast tier and `builder` on the standard tier in worktrees; on Codex the scout at low effort and the reviewer at high on the session model, with no project setup. The new autonomous integration, drift recovery, and owner-turn re-sizing rules in 1.14 remain `UNVERIFIED` until real runs exercise them.

What is still a design bet: that routing saves money (no paired delegated runs), that the reviewer on your session model catches what a stronger tier would, that the tagged-findings rule holds across many projects, and that less imposed process beats more on real work.

## Docs

- [Owner guide](docs/guide.md) and [how it works](docs/how-it-works.md)
- [Decisions](docs/decisions/README.md) and [research](docs/research/2026-08-26/README.md)
- [Contributing](CONTRIBUTING.md) and [security policy](SECURITY.md)
