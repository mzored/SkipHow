# Contributing

Use one issue for one material change when the repository workflow calls for tracking. Small coherent fixes do not need an issue solely because they modify code. Keep unrelated cleanup out of the same pull request.

## Before a pull request

- Keep intent and mutation routing in `plugins/skiphow/skills/skiphow/SKILL.md`.
- Put detailed workflow rules in the skill's `references/` directory. Codex and Claude must package the same canonical skill.
- Update the relevant research note and ADR when new evidence changes the architecture, product contract, security policy, or model routing. Do not save routine search notes.
- Add a rule only when it prevents a distinct demonstrated failure. Remove duplicated policy.
- Write direct English prose. Use concrete verbs, active voice, sentence-case headings, straight quotes, and short sentences. Remove promotional filler, vague claims, and unnecessary ceremony.
- Run focused checks while you work. Before completion, run `python scripts/check.py` and `git diff --check`.
- Let `scripts/check.py` create and reuse its environment outside the repository when the current Python lacks the pinned development dependencies.
- Run `python scripts/check_hosts.py` when packaging changed. Record exact host output for package support claims.
- Keep tests and CI local and deterministic. Do not launch Codex, Claude Code, or another model from them. Live outcome checks are separate, opt-in release work with an explicit budget.
- Do not add a runner, daemon, task database, provider adapter, or model catalog without a new accepted ADR based on a demonstrated host gap.

Explain the user-visible result, checks run, and any `UNVERIFIED` package evidence. A maintainer reviews the final integration diff before merge.
