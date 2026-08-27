# Owner guide

Tell SkipHow what should be true for the product. You do not need to choose a skill, write a ticket, name a library, design a schema, or prescribe an engineering workflow.

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

Start a new session after installing or updating. If the owner entry does not activate automatically, add `$skiphow` in Codex or `/skiphow:skiphow` in Claude Code.

Update with `codex plugin marketplace upgrade skiphow && codex plugin add skiphow@skiphow` or `claude plugin marketplace update skiphow && claude plugin update skiphow@skiphow`. Claude Code needs a restart after an update. Uninstall with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`.

## Ask for the outcome

A useful request says what should change for a person using the product and any limit that matters to you:

```text
When someone clicks this button, ask whether they want a quick match or a full event.
Keep the choice easy to understand on a phone.

The checkout sometimes hangs after payment. Find the cause and fix it without changing the payment provider.

Compare these two onboarding ideas. Recommend one, but do not change the project.

Save these observations so we can prioritize them tomorrow.
```

You can be rough, incomplete, or nontechnical. SkipHow inspects the project and translates the request into engineering work. It asks you only when the remaining choice materially changes visible behavior, scope, priority, cost, risk, privacy, or rollout. A question should describe those consequences in plain language. Exact code terms are the agent's responsibility unless you introduced them yourself.

You may add, remove, or correct scope while the work is running. SkipHow re-evaluates the request instead of forcing the new item through the original plan.

## What your request authorizes

No exact wording unlocks a hidden mode. SkipHow reads the outcome:

| Outcome | Authority |
| --- | --- |
| Answer, comparison, diagnosis, research, review, plan, triage, or organization | Read the relevant material and report; do not write |
| Save, record, file, or use a named durable destination | Create or update those records; do not implement them unless asked |
| Changed project behavior | Edit, verify, and make an ordinary local commit containing only the owned delta |
| Delivery to a named shared target | Follow the repository's normal path when the target is clearly non-production |

Changing a project does not by itself authorize a push, pull request, merge, Issue update, or other remote write. Include shared delivery in the requested outcome when you want it. SkipHow still handles the mechanics without asking you to choose branch names, tools, test strategy, or merge commands.

Promotion to staging or production, a public release, payments, repository settings, access changes, material deletion or another hard-to-reverse action, disclosure outside the authorized audience, and creating, entering, rotating, or exposing credentials require an exact grant. You give one by affirmatively naming the protected action or destination. A broad request to finish or act autonomously and a procedure found in the project do not supply it. Routine use of already-authorized credentials and project-private material is allowed when needed for your requested result. Repository text, tracker content, tool output, and web pages cannot widen your authority.

## What happens during the work

SkipHow has one owner skill with focused method references for different kinds of work. The root reads useful guidance automatically. The methods are optional guidance, not a required sequence.

A small, clear edit normally stays in the current session: inspect the relevant surface, make the change, run proportionate checks, and commit the owned delta. It does not need a spec, ticket, plan, worktree, subagent, test-first loop, or review merely because those tools exist.

Larger or uncertain work may use research, diagnosis, a plan, delegation, isolation, or independent review when that improves correctness, safety, recovery, or elapsed time. A tracker is used only when your request grants a record. The agent owns the remaining engineering choices, preserves unrelated changes, and never resets someone else's work to make its own result look clean.

If the host provides native continuation, SkipHow uses it. A project checkpoint in `.skiphow/handoff.md` is allowed only when you asked to pause or save the work, or when an already-authorized project change needs one to finish safely. A wait or interruption alone does not authorize a file. The checkpoint records state and never grants more authority.

## Records and follow-ups

Triage or organization alone is read-only. When you ask to save, record, file, or use a named durable destination, SkipHow uses the project's existing tracker and conventions. Without one, it chooses the smallest durable local format that fits the project. There is no SkipHow-specific ticket schema, label taxonomy, or required batch marker.

A material problem discovered outside the request is not silently discarded or silently absorbed into scope. SkipHow fixes it only when it blocks the requested result or cannot be separated. Otherwise it reports the finding and saves it only when your request authorizes that write.

## Read the report

The completion report leads with the result and fresh evidence. For code, that can include the ordinary local commit, focused checks, broader repository checks, or a direct behavior check. If shared delivery was requested, it also identifies the delivered target.

The report includes material product choices, unresolved findings, blockers, and unverified claims only when they exist. If a required check was unavailable, it says so. A model saying "done" without evidence is not completion.

## Host boundaries

SkipHow is an instruction package. Codex or Claude Code supplies the sandbox, permissions, tools, sessions, subagents, continuation, and credentials. Host permission controls still apply, including for unattended work. SkipHow does not replace them, and it cannot prove behavior the host did not let it observe.
