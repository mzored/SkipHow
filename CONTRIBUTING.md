# Contributing

SkipHow ships one canonical plugin for Codex and Claude Code: one autonomous owner skill with a dynamic library of focused Markdown methods. Keep changes small enough to review and large enough to solve one complete problem.

Read the [Code of Conduct](CODE_OF_CONDUCT.md) and use the [private security process](SECURITY.md) for vulnerabilities.

## Set up checks

The repository pins its check dependencies. Install them yourself, into whatever environment you run the checks from:

```sh
python -m pip install -r requirements-dev.txt
```

The checks never install anything and never reach a package index. An interpreter that does not satisfy the pins stops the run and names this command.

Run a focused test:

```sh
python scripts/check.py --pytest tests/test_package.py -q
```

The behavioral eval corpus in [`evals/`](evals/README.md) holds the cases for the behaviors 3.0.0 changed: the fixture, the prompt, and the events each case expects and forbids. Its shape is checked by `python scripts/check.py --pytest tests/test_evals_corpus.py -q`, which is deterministic, offline, and starts no model. Running a case is a different thing. It costs a real paid session, it gates nothing and no pull request needs one, and it happens only under the run limits in `evals/README.md` and with the owner's explicit authorization. Do not run one to check your own change.

## Change the canonical package

- Keep universal authority, autonomy, preservation, and completion invariants in the owner kernel at `plugins/skiphow/skills/skiphow/SKILL.md`.
- Put reusable task discipline in a focused Markdown reference under the owner skill. Keep authority, autonomy, preservation, and completion in the root; a method can help with technique, but a missed method must not change the grant or definition of done.
- Use linked resources for detail that can materially help only some tasks. Keep every Markdown file under the owner skill's `references/` library recursively reachable from `SKILL.md`.
- Keep Codex and Claude manifests pointed at the same `skills/` directory.
- Bump `VERSION` whenever `plugins/skiphow/` changes. Claude Code uses the manifest version as its update key.
- Update `docs/decisions.md` when evidence changes architecture, the product contract, or security policy. Update `docs/evidence.md` when supported claims or known limits change. Link to durable source material instead of adding one file per run or release.
- `scripts/check.py` validates one top-level owner skill, recursive reachability of every Markdown file under its `references/` library, the required continuity-hook metadata and accepted command shape, aligned versions, and the personal-path and provider-model-ID boundaries it scans. Do not reintroduce fixed method counts, role sets, model tiers, prose spellings, or word budgets. Record package-invariant changes and their evidence in `docs/decisions.md`, then update the check in the same change.
- Preserve upstream license, copyright, path, and inspected revision whenever a method copies or adapts source text. Record borrowed ideas and rejected alternatives in [the design](docs/design.md) and [decision history](docs/decisions.md).
- Write direct English prose. Use active voice, sentence-case headings, straight quotes, and concrete claims. Open each method with a scope line repeating the trigger `SKILL.md` carries for it, give any file over roughly four hundred words subheadings, keep one idea to a sentence, and use a list only where the content is already a set. No em dashes; prefer two sentences to a semicolon.

## Verify a pull request

Run focused checks while editing. Before completion, run:

```sh
python scripts/check.py
git diff --check
```

Run `python scripts/check_hosts.py` whenever packaging changes. Report an unavailable host as `UNVERIFIED`.
It runs the available hosts' package validators and, unless installation is skipped, attempts a
repository-free isolated install. A successful isolated install proves only that the host installed the
candidate's exact relative regular-file paths and SHA-256 contents from that local snapshot inside the fresh
isolated host home. Marketplace source paths are not installation proof. Validator and install results do not
prove model or session behavior.

Keep tests and CI local and deterministic. They must not start Codex, Claude Code, or another model. Behavior claims come from deliberate real-run receipts. Summarize the current claims and link their durable evidence in `docs/evidence.md`.

The pull request should state the user-visible result, scope, tests run, package evidence, and every material blocker or unverified limit. Keep unrelated cleanup out of the same pull request.

## Release

A release is three steps on `main`: bump `VERSION` and both plugin manifests, add the `## <version> (<date>)` section to `CHANGELOG.md`, then push the tag `v<version>`. The release workflow reruns the checks, refuses a tag that does not match `VERSION`, refuses a tag whose commit is not contained in `origin/main`, and publishes the GitHub release with that changelog section as its notes.
