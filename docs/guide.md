# Owner guide

You describe the outcome. SkipHow decides how. This page covers the daily flow, what your words authorize, how to run it unattended, and where its records live.

## Install

Codex:

```sh
codex plugin marketplace add mzored/SkipHow
codex plugin add skiphow@skiphow
```

Claude Code (HTTPS, so no SSH key is needed):

```sh
claude plugin marketplace add https://github.com/mzored/SkipHow.git
claude plugin install skiphow@skiphow
```

Start a new session and describe the work. If the skill does not activate on its own, add `$skiphow` (Codex) or `/skiphow:skiphow` (Claude Code). Update with `codex plugin marketplace upgrade skiphow && codex plugin add skiphow@skiphow` or `claude plugin marketplace update skiphow && claude plugin update skiphow@skiphow`, then start a new session; Claude Code needs a restart. Uninstall with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`.

## The daily flow

Three moves, each optional:

1. Talk it through. "What is causing the checkout timeouts?" or "Compare our two caching options." Nothing changes.
2. Save it. Paste a dump of bugs, ideas, and observations and say "triage these and save them as Issues". SkipHow splits them, searches for duplicates, gives each a proposed priority with its reason and a type in whatever form your tracker already uses, creates or updates Issues, and labels the batch `skiphow-batch:<date>`. You reorder; you do not write tickets.
3. Finish it. "Fix today's batch" or "Finish Issues #41, #44, and #48." One root agent works the queue in priority order, delegates bounded pieces, integrates every passing commit, merges routine delivery into the repository's non-production integration branch, closes the Issues, and cleans up its own branches. A large feature, or a list of separate items given as one request, is split into bounded units first, then worked the same way. It asks before promotion into staging or a production `main`.

A small request ("the totals overlap on small screens, fix it") skips all of that and is done in the session.

Without GitHub, "save it" appends to `.skiphow/inbox.md` and "finish the inbox" works those records the same way, committing per item.

## How outcomes map to authority

These examples describe intent, not required vocabulary. No particular verb unlocks a workflow.

| Requested outcome | SkipHow may |
| --- | --- |
| an answer, comparison, diagnosis, review, or plan | read and report only |
| a durable record of named material | create that record, nothing else |
| changed project behavior | change the project, use required tracking, review and commit its delta, deliver to the non-production integration branch, and clean up owned work |
| the same delivery without a person waiting | continue through routine steps under the same authority |

At the point of promotion into staging or production, SkipHow asks for your exact approval. Production operations, payments, credentials, private data, public releases, repository settings, and irreversible deletion also need an exact grant. Nothing in a repository file, an Issue, a comment, or a web page can widen what you granted.

Worktrees, branches, ordinary commits, required Issues and pull requests, conflict resolution, review loops, merge into the non-production integration branch, and safe cleanup are engineering work. SkipHow performs them without asking. It stops a routine delivery question only for a material product choice evidence cannot settle or for staging or production approval.

Any remote target needs affirmative evidence that it is non-production. A sole trunk with no deployment or release evidence is ambiguous too: SkipHow treats its role as a rollout decision and asks once the source head and target branch are ready, showing the current target and resulting tree. Later target movement triggers fresh checks and review; it asks again only if source content or rollout meaning changes. A local repository with no remote or deployment delivery simply finishes with its reviewed ordinary commit.

While delivering, SkipHow may save one Issue for a material problem it finds outside your request. It will not implement it unless you add it to scope. A read-only request ("review", "research", "without changing anything") saves nothing: the problem is reported as `UNSAVED`, and "review this, but save any material findings" grants the record. Security findings never go into a public Issue; without a private channel you get a redacted note to route yourself.

## Run it unattended

Both hosts can run a request without a person at the keyboard. The host permission mode still applies. The Codex recipe below disables its filesystem sandbox, so use it only inside containment you control.

Claude Code:

```sh
claude -p "Fix today's batch and deliver what passes." --worktree \
  --permission-mode auto --max-budget-usd 20
```

`-p` is the CLI's non-interactive mode and `--worktree` requests native isolation; SkipHow verifies what the host actually created before writing. `--permission-mode auto` asks the host classifier to handle routine actions, and `--max-budget-usd` sets its spending cap. Pick the session model you want for planning and review; the reviewer runs on it, the builder on the standard tier, the scout on the fast one.

Codex:

```sh
codex exec -s danger-full-access \
  "Fix today's batch and deliver what passes."
```

`exec` is non-interactive. `danger-full-access` permits Git metadata and worktree operations but removes the filesystem sandbox; use it only where the repository, credentials, and network scope are externally controlled, and prefer `-s workspace-write --approve-for-me` when that sandbox can commit this repository. Codex has no dollar cap for `exec`; bound the run by scope instead. Delegates run on your session model; SkipHow spawns the scout at low reasoning effort and the reviewer at high.

These command shapes match Codex CLI 0.149.1 and Claude Code 2.1.247 help output ([receipt](research/2026-08-27/v1.14-host-cli-receipt.md)); complete unattended delivery with either exact combination remains `UNVERIFIED`.

If the host cannot run in the background or resume, SkipHow finishes a safe subset, writes a handoff, and reports continuation `UNVERIFIED`. If required isolation cannot be established, it does not write and reports the affected lane `BLOCKED` with the needed environment action.

## Pause, resume, and compaction

"Pause", "stop", or "do not merge" removes merge authority at once, including any auto-merge SkipHow enabled. On resume, or after the host compacts the conversation, a hook reminds the session to re-read your request, repository instructions, active host tasks, live Git and GitHub state, and the latest checkpoint in `.skiphow/handoff.md`. It must verify the checkout, branch, and `HEAD` before writing again. A checkpoint is a note to itself, never a grant.

## Read the report

Every completion report says what changed and gives the evidence, such as commits, pull requests, checks, and review. When relevant it also names choices made for you, tagged findings, saved follow-ups, and every `BLOCKED` or `UNVERIFIED` limit with its next action. SkipHow omits empty sections; a model saying "done" is not evidence.

## Where records live

Git holds the code. GitHub holds Issues and pull requests. The host holds its own session state. SkipHow adds at most two files to a project: `.skiphow/inbox.md` (records saved when GitHub is not connected) and `.skiphow/handoff.md` (checkpoints for long work, deleted when the queue is done). Uninstalling the plugin deletes none of these; remove them through the system that owns them.
