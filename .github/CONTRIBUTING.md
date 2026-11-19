# Contributing

SkipHow ships one plugin for Codex and Claude Code: one accountable CTO kernel, optional workflow skills, and shared Markdown references. Keep each change small enough to review and large enough to solve one complete problem.

[AGENTS.md](../AGENTS.md) holds the contributor rules, and this page adds the commands, the package conventions, and the release mechanics. The package tells the agent to keep the owner's system small, in the kernel's [Engineering standard](../plugins/skiphow/skills/skiphow/SKILL.md#engineering-standard). Hold this repository to the same standard.

Read the [Code of Conduct](CODE_OF_CONDUCT.md), and report vulnerabilities through the [private security process](../SECURITY.md). The [README](../README.md#documentation) indexes the documentation.

## Set up checks

Install the pinned check dependencies into the environment you run the checks from:

```sh
python -m pip install -r requirements-dev.txt
```

The checks install nothing and never reach a package index. An interpreter that misses a pin stops the run and names this command.

Run a focused test:

```sh
python scripts/check.py --pytest tests/test_contract.py -q
```

`python scripts/check.py` is the gate. It rejects dated or version-qualified host mechanics in runtime Markdown, permits historical versions in maintainer evidence, and reports the ten slowest tests on stderr even when it passes. A direct `pytest tests` run is safe, because `tests/conftest.py` turns off bytecode writing before any test imports a shipped script. The package identity hashes every regular file under `plugins/skiphow/`, so a stray `__pycache__` there would change it.

`python scripts/check.py --pytest tests/test_evals_corpus.py -q` checks the shape of the [eval corpus](../evals/README.md) offline. Running a case is a paid model session. It gates nothing, no pull request needs one, and it happens only with the owner's authorization under the limits in `evals/README.md`.

## Change the package

- Universal authority, autonomy, preservation, engineering-standard, and completion invariants live in the kernel at `plugins/skiphow/skills/skiphow/SKILL.md`. A missed playbook must not change the grant or the definition of done.
- A workflow is a sibling skill with a distinct requested work pattern and stopping condition. It links the kernel by relative path and reuses the kernel's references instead of copying policy.
- Reusable method goes in a Markdown reference under the owner skill, reachable from `SKILL.md`. Open each one with a scope line that repeats the trigger `SKILL.md` carries for it.
- Both manifests point at the same `skills/` directory. Claude Code uses the manifest version as its update key, which is why `VERSION` moves whenever `plugins/skiphow/` changes.
- When a method copies or adapts source text, keep the upstream license, copyright, path, and inspected revision. Record borrowed ideas and rejected alternatives in [prior art](../docs/prior-art.md).
- When a package invariant changes, change `scripts/check.py` and [decisions](../docs/decisions.md) in the same change. Checks protect contracts, not wording, method counts, or layout.
- Write direct English prose: active voice, sentence-case headings, straight quotes, concrete claims, and one idea to a sentence. Give any file over roughly four hundred words subheadings. Use a list only where the content is already a set. Use no em dashes, and prefer two sentences to a semicolon.

## Verify a pull request

Run focused checks while editing. Before completion, run:

```sh
python scripts/check.py
git diff --check
```

Run `python scripts/check_hosts.py` whenever packaging changes, and report an unavailable host as `UNVERIFIED`. A successful isolated install proves only that the host installed the candidate's exact relative file paths and SHA-256 contents from that local snapshot into a fresh host home. Marketplace source paths are not installation proof, and neither result proves model or session behavior.

Tests and CI stay local and deterministic and never start a model. Behavior claims come from deliberate real-run receipts, and [`docs/evidence.md`](../docs/evidence.md) records each claim's status.

The pull request states the user-visible result, scope, tests run, package evidence, and every material blocker or unverified limit. Keep unrelated cleanup out of it.

## Release

A release branch bumps the version once, in `VERSION`, both plugin manifests, `package_under_test` in the three `evals/*.json` ledgers, and `site/evidence/index.html`, and adds the `## <version> (<date>)` section to `CHANGELOG.md`. After its pull request merges, push the tag `v<version>` on the merge commit. The release workflow runs three jobs with separate permissions:

- `validate` holds `contents: read`. It reruns the checks and the pinned Codex validator, refuses a tag that does not match `VERSION` or whose commit is not contained in `origin/main`, and uploads the release notes, the site, and the release validation matrix.
- `publish-release` holds `contents: write`, runs no repository code, and publishes the GitHub release from those notes.
- `deploy-site` publishes the validated site artifact of the same commit to Pages.

`pages.yml` is a manual repair that redeploys the site from one exact tag or commit SHA. Each release publishes the per-capability matrix that `scripts/check_hosts.py` prints. A skipped host stays `UNVERIFIED` in it and never folds into a green aggregate.
