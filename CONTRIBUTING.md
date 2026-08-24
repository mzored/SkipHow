# Contributing

Use one issue for one change. Start from an existing issue or open one with a clear problem statement, expected result, and scope. Keep unrelated cleanup out of the same pull request.

## Before you open a pull request

- Keep skill policy in the canonical `plugins/skiphow/skills/cto-run/` directory. The Claude Code adapter must remain a small link to that workflow.
- Add or update tests before you claim a behavior works. Run the focused test first, then the repository suite when the change reaches an integration point.
- Run `git diff --check` and fix whitespace errors.
- Use current host documentation and record reproducible Codex or Claude Code support evidence when the change affects packaging or `cto-run`.
- Apply the `unslop` skill to repository text. Write direct English prose. Do not add em dashes, promotional filler, or vague claims.

## Pull requests

Explain the user-visible change, tests run, and evidence for each support claim. Call out changes to the canonical workflow, adapter, manifests, or durable state contract. A maintainer reviews the final integration diff before merge.
