# Contributing

Use one issue for one material change when the repository workflow calls for tracking. Small coherent fixes do not need an issue solely because they modify code. Keep unrelated cleanup out of the same pull request.

## Before a pull request

- Keep intent and mutation routing in `plugins/skiphow/skills/skiphow/SKILL.md`.
- Keep product, technical, campaign, and tracker policy in their owned reference directories. The Claude adapter must remain a short link to the canonical skill.
- Add a rule only when it prevents a distinct demonstrated failure. Remove duplicated policy.
- Write direct English prose. Use concrete verbs, active voice, sentence-case headings, straight quotes, and short sentences. Remove promotional filler, vague claims, and unnecessary ceremony.
- Run focused tests with `python scripts/check.py --pytest <pytest-arguments>`, then `python scripts/check.py --base <base-sha>` at integration.
- Let `scripts/check.py` create and reuse the ignored `.venv` when the current Python lacks the pinned development dependencies.
- Run `python scripts/check_hosts.py` when packaging changed. Record exact host output for package support claims.
- Do not launch Codex, Claude Code, or another model from tests or release checks. The repository has no live model eval gate.

Explain the user-visible result, checks run, and any `UNVERIFIED` package evidence. A maintainer reviews the final integration diff before merge.
