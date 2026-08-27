# Contributing

SkipHow ships one canonical plugin for Codex and Claude Code: one autonomous owner skill with a dynamic library of focused Markdown methods. Keep changes small enough to review and large enough to solve one complete problem.

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

- Keep universal authority, autonomy, preservation, and completion invariants in the owner kernel at `plugins/skiphow/skills/skiphow/SKILL.md`.
- Put reusable task discipline in a focused Markdown reference under the owner skill. Keep authority, autonomy, preservation, and completion in the root; a missed method may reduce technique quality but must not change the grant or definition of done.
- Use linked resources for detail that should load only when it helps. Keep every shipped resource reachable from the owner skill.
- Keep Codex and Claude manifests pointed at the same `skills/` directory.
- Bump `VERSION` whenever `plugins/skiphow/` changes. Claude Code uses the manifest version as its update key.
- Update research and an ADR when evidence changes architecture, the product contract, or security policy.
- `scripts/check.py` validates the one-skill package, dynamically reachable resources, the continuity hook, aligned versions, and portability boundaries. Do not reintroduce fixed method counts, role sets, model tiers, prose spellings, or word budgets. Change package invariants with an ADR that records the evidence and update the check in the same change.
- Preserve upstream license, copyright, path, and inspected revision whenever a method copies or adapts source text. Credit borrowed ideas in [prior art](docs/prior-art.md).
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

The pull request should state the user-visible result, scope, tests run, package evidence, and every material blocker or unverified limit. Keep unrelated cleanup out of the same pull request.

## Release

A release is three steps on `main`: bump `VERSION` and both plugin manifests, add the `## <version> (<date>)` section to `CHANGELOG.md`, then push the tag `v<version>`. The release workflow reruns the checks, refuses a tag that does not match `VERSION`, refuses a tag whose commit is not contained in `origin/main`, and publishes the GitHub release with that changelog section as its notes.
