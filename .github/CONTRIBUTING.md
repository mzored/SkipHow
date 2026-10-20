# Contributing

SkipHow ships one canonical plugin for Codex and Claude Code: one accountable CTO kernel, optional workflow skills, and shared Markdown references. Keep each change small enough to review and large enough to solve one complete problem.

The package tells the agent to keep the owner's system small. It builds the least that delivers the outcome, writes a test only for a break a user or caller would notice, and removes what no longer pays for itself. Guards for money, security, customer data, and the release path stay. The kernel's Engineering standard section carries these rules, and the lead pastes it into every implementation and review brief because delegates do not inherit the skill. Hold this repository to the same standard.

Read the [Code of Conduct](CODE_OF_CONDUCT.md), and report vulnerabilities through the [private security process](../SECURITY.md). [AGENTS.md](../AGENTS.md) holds the full contributor rules, and the [README](../README.md#documentation) indexes the documentation.

## Set up checks

The repository pins its check dependencies. Install them into the environment you run the checks from:

```sh
python -m pip install -r requirements-dev.txt
```

The checks never install anything and never reach a package index. An interpreter that misses a pin stops the run and names this command.

Run a focused test:

```sh
python scripts/check.py --pytest tests/test_package.py -q
```

A direct `pytest tests` run is safe too. `tests/conftest.py` turns off bytecode writing before any test imports a shipped script. The package identity in `scripts/check_hosts.py` hashes every regular file under `plugins/skiphow/` by design, so a stray `__pycache__` directory there would change it. `python scripts/check.py` stays the gate. It rejects dated or version-qualified host mechanics in runtime Markdown, permits historical versions in maintainer evidence, and reports the ten slowest tests on stderr even when it passes.

The behavioral eval corpus in [`evals/`](../evals/README.md) holds the behavioral cases: the fixture, the prompt, and the events each case expects and forbids. `python scripts/check.py --pytest tests/test_evals_corpus.py -q` checks its shape. That check is deterministic and offline and starts no model. Running a case is different. It costs a real paid session, gates nothing, and no pull request needs one. It happens only under the run limits in `evals/README.md` and with the owner's explicit authorization. Do not run one to check your own change.

## Change the canonical package

- Keep universal authority, autonomy, preservation, engineering-standard, and completion invariants in the owner kernel at `plugins/skiphow/skills/skiphow/SKILL.md`.
- Put an optional workflow in a sibling skill only when it defines a distinct requested work pattern and stopping condition. Require the CTO kernel in context through a relative link before consequential work. Reuse the kernel's references instead of duplicating policy. A declared dependency proves no model loading.
- Put reusable task discipline in a focused Markdown reference under the owner skill. Keep authority, autonomy, preservation, and completion in the root. A method can help with technique, but a missed method must not change the grant or the definition of done.
- Use linked resources for detail that materially helps only some tasks. Keep every Markdown file in the owner skill's `references/` library recursively reachable from `SKILL.md`.
- Keep the Codex and Claude manifests pointed at the same `skills/` directory.
- Bump `VERSION` whenever `plugins/skiphow/` changes. Claude Code uses the manifest version as its update key.
- Follow the documentation rules in `AGENTS.md`: `docs/` describes the current state, and per-release motivation goes in `CHANGELOG.md`. Link durable source material instead of adding one file per run or release.
- `scripts/check.py` validates the required CTO entry, sibling workflow links to it, recursive reachability of Markdown references, the safety shape of any shipped hook, aligned versions, and the personal-path and provider-model-ID boundaries it scans. Do not reintroduce fixed method counts, role sets, model tiers, prose spellings, marketing sentences, matcher topology, site presentation details, or word budgets. The assertion classes in `AGENTS.md` make those editorial preferences, at most a non-blocking lint. When a package invariant changes, record it and its evidence in `docs/decisions.md` and update the check in the same change.
- When a method copies or adapts source text, preserve the upstream license, copyright, path, and inspected revision. Record borrowed ideas and rejected alternatives in [prior art](../docs/prior-art.md) and, when they change a decision, in [decisions](../docs/decisions.md).
- Write direct English prose. Use active voice, sentence-case headings, straight quotes, and concrete claims. Open each method with a scope line that repeats the trigger `SKILL.md` carries for it. Give any file over roughly four hundred words subheadings. Keep one idea to a sentence, and use a list only where the content is already a set. Use no em dashes, and prefer two sentences to a semicolon.

## Verify a pull request

Run focused checks while editing. Before completion, run:

```sh
python scripts/check.py
git diff --check
```

Run `python scripts/check_hosts.py` whenever packaging changes, and report an unavailable host as `UNVERIFIED`. It runs the available hosts' package validators and, unless installation is skipped, attempts a repository-free isolated install. A successful isolated install proves only that the host installed the candidate's exact relative regular-file paths and SHA-256 contents from that local snapshot inside the fresh isolated host home. Marketplace source paths are not installation proof. Validator and install results do not prove model or session behavior.

Keep tests and CI local and deterministic. They must not start Codex, Claude Code, or another model. Behavior claims come from deliberate real-run receipts. `docs/evidence.md` records each claim's current status with links to its durable evidence.

The pull request states the user-visible result, scope, tests run, package evidence, and every material blocker or unverified limit. Keep unrelated cleanup out of it.

## Release

A release is three steps on `main`: bump `VERSION` and both plugin manifests, add the `## <version> (<date>)` section to `CHANGELOG.md`, then push the tag `v<version>`. The release workflow runs three jobs with separate permissions:

- `validate` holds `contents: read`. It reruns the checks and the pinned Codex validator, refuses a tag that does not match `VERSION` or whose commit is not contained in `origin/main`, and uploads the release notes, the site, and the release validation matrix.
- `publish-release` holds `contents: write`, runs no repository code, and publishes the GitHub release from those notes.
- `deploy-site` publishes the validated site artifact of the same commit to Pages.

`pages.yml` is a manual repair that redeploys the site from one exact tag or commit SHA and nothing else. Each release publishes the per-capability matrix that `scripts/check_hosts.py` prints. A skipped host stays `UNVERIFIED` in it and never folds into a green aggregate.
