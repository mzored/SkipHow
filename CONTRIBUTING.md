# Contributing

Use one issue for one material change when the repository workflow calls for tracking. Small coherent fixes do not need an issue solely because they modify code. Keep unrelated cleanup out of the same pull request.

## Before a pull request

- Keep intent and mutation routing in `plugins/skiphow/skills/skiphow/SKILL.md`.
- Keep product, technical, campaign, and tracker policy in their owned reference directories. The Claude adapter must remain a short link to the canonical skill.
- Add a rule only when it prevents a distinct demonstrated failure. Remove duplicated policy.
- Write direct English prose. Use concrete verbs, active voice, sentence-case headings, straight quotes, and short sentences. Remove promotional filler, vague claims, and unnecessary ceremony.
- Run the focused check while iterating, then `python scripts/check.py --base <base-sha>` at integration.
- Run `python scripts/check_hosts.py` when packaging or campaign support changed. Record exact host output for support claims.

Explain the user-visible result, checks run, and any `UNVERIFIED` host evidence. A maintainer reviews the final integration diff before merge.
