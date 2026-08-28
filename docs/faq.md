# Frequently asked questions

Short answers about installing and using SkipHow. The [owner guide](guide.md) has the long version, and [current evidence](evidence.md) says which of these behaviors real runs have shown.

## What is SkipHow?

SkipHow is one Agent Skill for Claude Code and OpenAI Codex. You describe what should be true for the product in ordinary language, and the agent inspects the project, makes the engineering decisions, verifies the result, and reports what the evidence proves. It ships as a plugin containing a single skill: no server, no database, no separate runtime.

## Which agents does it work with?

Claude Code and OpenAI Codex. Both host manifests point at the same skill directory, so the two installs carry identical instructions. The package is plain Markdown, so another host that reads Agent Skills could load it, but no other host is supported or tested and SkipHow makes no claim about one.

## Do I need to know how to code?

No. You need a repository and one of the two hosts. SkipHow is written for the person who owns what the product should do, and it will not ask you to pick a library, a schema, a branch strategy or a test command. If a question comes back to you, it is about visible behavior, priority, cost, risk, privacy or rollout, in plain language, with a recommendation.

## How is SkipHow different from OpenSpec, BMAD or Superpowers?

Those frameworks give you a workflow to drive: commands, phases, specs, tickets, approval gates. SkipHow states a contract and leaves the sequence to the agent, so there is nothing for you to operate. The tradeoff is real. If you want to control the method yourself, one of those projects fits you better. [Prior art](prior-art.md) records what SkipHow borrowed from each and what it dropped.

## Will it push, merge or deploy without asking?

No. A request to change the project covers edits, checks and a clean local commit. Anything shared has to be asked for. Production, staging, public releases, payments, credentials, repository settings, access changes and destructive actions need a grant that names them in your own request. Instructions inside a file, an issue, a tool result or a web page cannot widen that.

## What happens to work I did not ask about?

It stays untouched. A dirty working tree stops a commit only when the owned change cannot be separated safely. A material problem found along the way is either fixed, if it blocks the work, or recorded where your project already tracks work, so the next session picks it up instead of rediscovering it.

## Where does it keep tasks and findings?

In your project's own tracker. The first time a project needs to record something, SkipHow asks once where records should live and who may see them, writes that answer into the project's instructions, and follows it from then on. It uses the tracker's own classification and does not introduce a schema of its own.

## Does it need GitHub?

No. Git is enough for a local commit, and any tracker your project already uses is enough for records. GitHub Issues is one option among them, not a requirement.

## When does it ask me a question?

Only when the answer changes what a person using the product gets and the project's own evidence cannot settle it. Everything answerable at that moment arrives together rather than one message at a time. If your answer opens a choice nobody could have put to you earlier, that comes back in a second round. While a question is with you it does not build one of the answers behind a default or a feature switch, and the parts that do not depend on your answer carry on.

## Does it run work in parallel?

It splits work that carries more than one independently verifiable outcome, with only the dependencies that genuinely block one another. That split is what the receipts show. Running the parts concurrently through delegates and worktrees is the intent, and no run has demonstrated it yet, so it stays `UNVERIFIED` in [current evidence](evidence.md).

## How much of my context does it use?

The kernel is about 1,600 words and stays in context. Eighteen focused methods, about 6,800 words in total, load only when a request reaches them. Receipts show methods loading in proportion to the work rather than on every request.

## Does it send my code anywhere?

SkipHow adds no network calls, no telemetry and no credentials. It is Markdown instructions. Whatever your host already sends to its own model provider is unchanged by installing it, and the repository's checks scan the package for personal paths and provider model IDs on every run.

## What does `UNVERIFIED` mean in a report?

It means no run has shown that behavior, so the claim is not being made. SkipHow separates deterministic package checks, which prove structure, from receipts, which are real runs on throwaway fixtures. A behavior with no receipt is labelled rather than described as working. The current list of unproven behaviors is in [current evidence](evidence.md).

## How do I update or uninstall it?

Update with `codex plugin marketplace upgrade skiphow` then `codex plugin add skiphow@skiphow`, or `claude plugin marketplace update skiphow` then `claude plugin update skiphow@skiphow`. Remove with `codex plugin remove skiphow@skiphow` or `claude plugin uninstall skiphow@skiphow`. Start a new session after either.

## The skill did not load. What now?

Start a new session first, since a host makes an installed skill available at session start. If it still does not load on its own, name it: `$skiphow` in Codex, `/skiphow:skiphow` in Claude Code.

## Is it free?

Yes, MIT licensed. You pay your host for the model usage, as you would without it.
