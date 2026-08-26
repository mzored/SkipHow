# Contributing

SkipHow ships one canonical skill for Codex and Claude Code. Keep changes small enough to review and large enough to solve one complete problem.

Read the [Code of Conduct](CODE_OF_CONDUCT.md) and use the [private security process](SECURITY.md) for vulnerabilities.

## Set up checks

The repository uses pinned Python dependencies in a cached environment outside the checkout. Prepare it and print its interpreter path:

```sh
python scripts/check.py --prepare-only
```

Run a focused test through that environment:

```sh
python scripts/check.py --pytest tests/test_repository.py -q
```

## Change the canonical package

- Keep intent and route selection in `plugins/skiphow/skills/skiphow/SKILL.md`.
- Put conditional detail in linked references. Do not add another public skill for an internal method.
- Keep Codex and Claude manifests pointed at the same `skills/` directory.
- Bump `VERSION` whenever `plugins/skiphow/` changes. Claude Code uses the manifest version as its update key.
- Update research and an ADR when evidence changes architecture, the product contract, security policy, or model routing.
- Do not add a runner, daemon, task database, provider adapter, model catalog, telemetry, or personal configuration without an accepted product decision. The only permitted hook is the continuity hook in `plugins/skiphow/hooks/hooks.json` (ADR 0007 and 0010); the only agents are the three role adapters in `plugins/skiphow/agents/`.
- Write direct English prose. Use active voice, sentence-case headings, straight quotes, and concrete claims.

## Verify a pull request

Run focused checks while editing. Before completion, run:

```sh
python scripts/check.py
python scripts/check_hosts.py
git diff --check
```

Run `python scripts/check_hosts.py` whenever packaging changes. Report an unavailable host as `UNVERIFIED`. Host validation proves package loading, not model behavior.

Keep tests and CI local and deterministic. They must not start Codex, Claude Code, or another model. Behavior claims come from receipts under `docs/research/<date>/` written after a real run (ADR 0008).

The pull request should state the user-visible result, scope, tests run, package evidence, and every material `BLOCKED` or `UNVERIFIED` limit. Keep unrelated cleanup out of the same pull request.

## Release

A release is three steps on `main`: bump `VERSION` and both plugin manifests, add the `## <version> (<date>)` section to `CHANGELOG.md`, then push the tag `v<version>`. The release workflow reruns the checks, refuses a tag that does not match `VERSION`, and publishes the GitHub release with that changelog section as its notes.
