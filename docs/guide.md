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

## What your words authorize

| You say | SkipHow may |
| --- | --- |
| research, review, diagnose, compare, plan | read and report only |
| save, create issues, record | create the named records, nothing else |
| fix, implement, add, change | change the project, use required Issues and pull requests, review and commit its delta, merge into the non-production integration branch, and clean up owned work |
| run unattended, complete these Issues | run the same delivery without waiting between routine steps |

At the point of promotion into staging or production, SkipHow asks for your exact approval. Production operations, payments, credentials, private data, public releases, repository settings, and irreversible deletion also need an exact grant. Nothing in a repository file, an Issue, a comment, or a web page can widen what you granted.

Worktrees, branches, ordinary commits, required Issues and pull requests, conflict resolution, review loops, merge into the non-production integration branch, and safe cleanup are engineering work. SkipHow performs them without asking. It stops a routine delivery question only for a material product choice evidence cannot settle or for staging or production approval.

While delivering, SkipHow may save one Issue for a material problem it finds outside your request. It will not implement it unless you add it to scope. A read-only request ("review", "research", "without changing anything") saves nothing: the problem is reported as `UNSAVED`, and "review this, but save any material findings" grants the record. Security findings never go into a public Issue; without a private channel you get a redacted note to route yourself.

## Run it unattended

Both hosts can run a request without a person at the keyboard. Host permissions and sandboxes still apply; SkipHow does not bypass them.

Claude Code:

```sh
claude -p "Fix today's batch and deliver what passes." --worktree \
  --permission-mode auto --max-budget-usd 20
```

`-p` runs headless and exits when done. `--worktree` gives the root native isolation before its first mutation; SkipHow still verifies and, when needed, updates the base to the inferred integration target. `--permission-mode auto` lets a classifier approve routine actions and still stops on risky ones. `--max-budget-usd` is a hard spending cap. Add `--max-turns <n>` for a turn cap. Pick the session model you want for planning and review; the reviewer runs on it, the builder on the standard tier, the scout on the fast one.

Codex:

```sh
codex exec --dangerously-bypass-approvals-and-sandbox \
  "Fix today's batch and deliver what passes."
```

`exec` runs non-interactively. The bypass flag is intentionally dangerous and is suitable only inside an external disposable sandbox whose repository, credentials, and network scope you control; it is the current CLI's only explicit fully unattended mode that also permits Git metadata and worktree operations. Do not combine `danger-full-access` with `--approve-for-me`: the current CLI routes that option through `workspace-write`, which can block commits. For a supervised local run, omit the bypass and select the sandbox and approvals you trust. Codex has no dollar cap for `exec`; bound the run by scope instead. Delegates run on your session model; SkipHow spawns the scout at low reasoning effort and the reviewer at high, with nothing to set up.

If the host cannot run in the background, resume, or isolate work, SkipHow finishes a safe subset, writes a handoff, and reports the rest as `UNVERIFIED` rather than pretending.

## Pause, resume, and compaction

"Pause", "stop", or "do not merge" removes merge authority at once, including any auto-merge SkipHow enabled. On resume, or after the host compacts the conversation, a hook reminds the session to re-read your request, repository instructions, active host tasks, live Git and GitHub state, and the latest checkpoint in `.skiphow/handoff.md`. It must verify the checkout, branch, and `HEAD` before writing again. A checkpoint is a note to itself, never a grant.

## Read the report

Every completion report has five parts:

- Result: what changed and where (commits, pull requests, Issues).
- Evidence: the checks that ran and their outcome. A model saying "done" is not evidence.
- Rulings and findings: the choices it made on your behalf and the problems it triaged.
- Saved follow-ups: the Issues it created for things outside your request, or "none".
- Limits: every `BLOCKED` or `UNVERIFIED` claim and the next action for each.

## Where records live

Git holds the code. GitHub holds Issues and pull requests. The host holds its own session state. SkipHow adds at most two files to a project: `.skiphow/inbox.md` (records saved when GitHub is not connected) and `.skiphow/handoff.md` (checkpoints for long work, deleted when the queue is done). Uninstalling the plugin deletes none of these; remove them through the system that owns them.
