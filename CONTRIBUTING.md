# Contributing

Use one issue for one change. Start from an existing issue or open one with a clear problem statement, expected result, and scope. Keep unrelated cleanup out of the same pull request.

## Before you open a pull request

- Keep shared technical policy in `plugins/skiphow/skills/cto/` and durable runtime policy in `plugins/skiphow/skills/cto-run/`. Claude Code adapters must remain small links to canonical workflows.
- Add or update tests before you claim a behavior works. Run the focused test first, then the repository suite when the change reaches an integration point.
- Run `python scripts/verify_release.py --base <base-sha>` at the integration boundary. It includes the repository suite, metadata and link validation, the source scan, behavioral corpus validation, and whitespace checks for the working tree and full candidate diff.
- Use current host documentation and record reproducible Codex or Claude Code support evidence when the change affects packaging or `cto-run`.
- Apply the `unslop` skill to repository text. Write direct English prose. Do not add em dashes, promotional filler, or vague claims.

## Pull requests

Explain the user-visible change, tests run, and evidence for each support claim. Call out changes to the canonical workflow, adapter, manifests, or durable state contract. A maintainer reviews the final integration diff before merge.
