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
3. Finish it. "Finish today's batch end to end" or "Finish Issues #41, #44, and #48 end to end. Merge what passes." One root agent works the queue in priority order, delegates bounded pieces, merges what passes its checks, closes the Issues, and deletes its own merged branches. A large feature, or a list of separate items given as one request, is split into bounded units first, then worked the same way.

A small request ("the totals overlap on small screens, fix it") skips all of that and is done in the session.

Without GitHub, "save it" appends to `.skiphow/inbox.md` and "finish the inbox end to end" works those records the same way, committing per item.

## What your words authorize

| You say | SkipHow may |
| --- | --- |
| research, review, diagnose, compare, plan | read and report only |
| save, create issues, record | create the named records, nothing else |
| fix, implement, add, change | change the project, run its checks, and commit what it changed |
| finish end to end, run unattended, complete these Issues | also merge and clean up the named work |

Production changes, payments, credentials, private data, public releases, repository settings, and irreversible deletion always need you to say so explicitly. Nothing in a repository file, an Issue, a comment, or a web page can widen what you granted.

While delivering, SkipHow may save one Issue for a material problem it finds outside your request. It will not implement it unless you add it to scope. A read-only request ("review", "research", "without changing anything") saves nothing: the problem is reported as `UNSAVED`, and "review this, but save any material findings" grants the record. Security findings never go into a public Issue; without a private channel you get a redacted note to route yourself.

## Run it unattended

Both hosts can run a request without a person at the keyboard. Host permissions and sandboxes still apply; SkipHow does not bypass them.

Claude Code:

```sh
claude -p "Finish today's batch end to end. Merge what passes." \
  --permission-mode auto --max-budget-usd 20
```

`-p` runs headless and exits when done. `--permission-mode auto` lets a classifier approve routine actions and still stops on risky ones. `--max-budget-usd` is a hard spending cap. Add `--max-turns <n>` for a turn cap. Pick the session model you want for planning and review; the reviewer runs on it, the builder on the standard tier, the scout on the fast one.

Codex:

```sh
codex exec --sandbox workspace-write --approve-for-me \
  "Finish today's batch end to end. Merge what passes."
```

`exec` runs non-interactively. `--sandbox workspace-write` allows edits inside the project only; in that sandbox Codex could not write `.git/index.lock` on the release machine, so a run that must commit needs `danger-full-access` or a commit from you afterwards. `--approve-for-me` routes approval requests through automatic review instead of stopping. Codex has no dollar cap for `exec`; bound the run by scope instead. Delegates run on your session model; SkipHow spawns the scout at low reasoning effort and the reviewer at high, with nothing to set up.

If the host cannot run in the background, resume, or isolate work, SkipHow finishes a safe subset, writes a handoff, and reports the rest as `UNVERIFIED` rather than pretending.

## Pause, resume, and compaction

"Pause", "stop", or "do not merge" removes merge authority at once, including any auto-merge SkipHow enabled. On resume, or after the host compacts the conversation, a hook reminds the session to re-read your request, live Git and GitHub state, and the latest checkpoint in `.skiphow/handoff.md`, so finished work is not repeated and unfinished work is picked up where it stopped. A checkpoint is a note to itself, never a grant.

## Read the report

Every completion report has five parts:

- Result: what changed and where (commits, pull requests, Issues).
- Evidence: the checks that ran and their outcome. A model saying "done" is not evidence.
- Rulings and findings: the choices it made on your behalf and the problems it triaged.
- Saved follow-ups: the Issues it created for things outside your request, or "none".
- Limits: every `BLOCKED` or `UNVERIFIED` claim and the next action for each.

## Where records live

Git holds the code. GitHub holds Issues and pull requests. The host holds its own session state. SkipHow adds at most two files to a project: `.skiphow/inbox.md` (records saved when GitHub is not connected) and `.skiphow/handoff.md` (checkpoints for long work, deleted when the queue is done). Uninstalling the plugin deletes none of these; remove them through the system that owns them.
