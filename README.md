# SkipHow

Describe the product outcome. SkipHow handles the engineering.

```text
The totals overlap on small screens. Find the cause and fix it.

Compare our caching options and recommend one. Do not change code.
```

SkipHow gives Codex and Claude Code one owner-facing skill. You describe what should be true for the product. The agent inspects the project, makes the technical decisions, verifies the result, and reports what the evidence proves.

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

Start a new session after installation. The [plugin guide](https://learn.chatgpt.com/docs/plugins) explains why installed skills become available in new sessions.

## Use it

Ask for the outcome in ordinary language. Add the limits that matter to you.

```text
When someone clicks this button, ask whether they want a quick match or a full event.
Keep the choice clear on a phone.

Here are today's bugs and ideas. Triage and save them.

Review this change and fix any real problems you find.
```

You decide visible behavior, priority, cost, risk, privacy, and rollout. SkipHow owns libraries, schemas, tests, branches, and other engineering choices.

## What it does

- Read-only requests stay read-only.
- Project changes include fresh checks and a clean local commit when the repository allows one.
- Remote delivery happens only when you ask for shared delivery.
- Production, public releases, credentials, payments, access changes, and destructive actions need an explicit grant.
- A problem found along the way is fixed, or recorded where your project tracks work, so the next session picks it up.
- Large work is split into parts you can each see working, and independent parts can run at the same time.
- Unrelated work stays untouched. Missing evidence stays `UNVERIFIED`.

SkipHow is an instruction package, not a workflow engine. It ships one owner skill with a small kernel and focused internal methods. The host still controls permissions, tools, sessions, and credentials.

## Read more

- [Owner guide](docs/guide.md)
- [Design](docs/design.md)
- [Decision history](docs/decisions.md)
- [Current evidence](docs/evidence.md)
- [Contributing](CONTRIBUTING.md)

SkipHow adapts selected ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills). The package keeps the required MIT attribution in [`THIRD_PARTY_NOTICES.md`](plugins/skiphow/THIRD_PARTY_NOTICES.md).
