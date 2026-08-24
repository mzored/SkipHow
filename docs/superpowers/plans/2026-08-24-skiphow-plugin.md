# SkipHow plugin implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish SkipHow `0.1.0` as a skills-only plugin that runs `cto-run` in Codex and Claude Code from one portable operating policy.

**Architecture:** Keep the standard Agent Skills entrypoint in `skills/cto-run/`. Codex loads it directly and controls invocation through `agents/openai.yaml`. Claude Code loads a thin adapter through its manifest, while both hosts read the same packaged policy, state contract, routing rules, and runbook template.

**Tech stack:** Markdown, JSON, YAML, Python 3.11, PyYAML 6.0.3, GitHub Actions, Codex CLI, Claude Code CLI.

**Spec:** `docs/superpowers/specs/2026-08-24-skiphow-plugin-design.md`

## Global constraints

- Codex and Claude Code are supported in `0.1.0`.
- `cto-run` must require explicit user invocation in both hosts.
- No MCP server, hooks, telemetry, remote service, credential flow, or runtime dependency.
- No maintainer-specific absolute path or preinstalled personal helper.
- The portable policy names capability roles, not vendor model names.
- Host policy and repository instructions outrank the skill.
- English is the source language for repository text.
- Apply `unslop` to every public text file.
- MIT license.
- One writer owns each file set. Integration remains serial.
- Completion claims require fresh evidence for the exact candidate commit.

---

### Task 1: Publish the design baseline and claim the work

**Files:**
- Existing: `docs/superpowers/specs/2026-08-24-skiphow-plugin-design.md`
- Existing: `docs/superpowers/plans/2026-08-24-skiphow-plugin.md`

**Interfaces:**
- Consumes: local `main` with the design commit.
- Produces: public `mzored/SkipHow`, a linked Project v2 board, issue `#1`, and an isolated issue worktree.

- [ ] **Step 1: Verify the baseline**

Run:

```bash
git status --short --branch
git log --oneline --decorate -2
git diff --check
```

Expected: `main` is clean and contains separate design and plan commits.

- [ ] **Step 2: Create and configure the public repository**

Run:

```bash
gh repo create mzored/SkipHow --public --source=. --remote=origin --push \
  --description "Skills for long-running software work in Codex and Claude Code"
gh repo edit mzored/SkipHow --enable-issues --enable-wiki=false \
  --add-topic agent-skills --add-topic claude-code --add-topic codex \
  --add-topic orchestration --add-topic plugins
```

Expected: `gh repo view mzored/SkipHow --json visibility,url` reports `PUBLIC`.

- [ ] **Step 3: Create and link the project board**

Create a public Project v2 named `SkipHow`. Keep the default `Status` field with `Todo`, `In Progress`, and `Done`. Add a `Human Gate` single-select field with `No`, `Deploy`, `Product decision`, and `External`. Link the repository to the project and verify `gh-task-status board mzored/SkipHow` resolves one board.

- [ ] **Step 4: File the release issue**

Create a Task issue with this exact contract:

```markdown
## Goal

Publish SkipHow 0.1.0 with cto-run working in Codex and Claude Code from one portable policy.

## Success criteria

- [ ] Codex and Claude Code install the plugin from this repository.
- [ ] cto-run requires explicit invocation in both hosts.
- [ ] Repository tests and both host validators pass.
- [ ] Release v0.1.0 is public.

## Context

Design: docs/superpowers/specs/2026-08-24-skiphow-plugin-design.md
Plan: docs/superpowers/plans/2026-08-24-skiphow-plugin.md
```

Add the issue to the project.

- [ ] **Step 5: Create the issue branch and worktree**

Use `gh issue develop` with branch name `1-publish-skiphow-0-1-0`, then create or select the isolated worktree through `superpowers:using-git-worktrees`. Confirm the worktree starts from the design and plan commits.

### Task 2: Add the repository contract and plugin skeleton

**Files:**
- Create: `tests/test_repository.py`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `.gitattributes`
- Create: `.editorconfig`
- Create: `.codex-plugin/plugin.json`
- Create: `skills/cto-run/SKILL.md`
- Create: `skills/cto-run/agents/openai.yaml`
- Create: `README.md`
- Create: `LICENSE`

**Interfaces:**
- Consumes: version `0.1.0`, plugin name `skiphow`, canonical skill path `skills/cto-run`.
- Produces: `load_json(path: str) -> dict`, `load_frontmatter(path: str) -> dict`, and the initial Codex plugin structure.

- [ ] **Step 1: Scaffold with the official creators**

Run the bundled plugin creator in a temporary directory with `--with-skills`. Run the bundled skill initializer for `cto-run`. Keep their generated manifests as schema references. Do not copy placeholders or personal marketplace entries into the repository.

- [ ] **Step 2: Write the failing repository test**

Create `tests/test_repository.py` with helpers based on `json.loads` and `yaml.safe_load`. Add `RepositoryContractTests.test_required_structure` that checks these paths:

```python
REQUIRED_PATHS = {
    ".codex-plugin/plugin.json",
    "skills/cto-run/SKILL.md",
    "skills/cto-run/agents/openai.yaml",
    "README.md",
    "LICENSE",
}
```

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_required_structure -v
```

Expected: FAIL because `README.md` and `LICENSE` do not exist.

- [ ] **Step 3: Add the minimal skeleton**

Create the listed configuration files. Pin `PyYAML==6.0.3` in `requirements-dev.txt`. Set the plugin manifest to `name: skiphow`, `version: 0.1.0`, `skills: ./skills/`, repository `https://github.com/mzored/SkipHow`, and license `MIT`. Set `agents/openai.yaml` to:

```yaml
interface:
  display_name: CTO Run
  short_description: Run long software campaigns with durable state
  default_prompt: Start or resume this project's CTO run.
policy:
  allow_implicit_invocation: false
```

Create minimal `README.md` and `LICENSE` files so the structure test can turn green. Later tasks replace the README with complete public documentation.

- [ ] **Step 4: Run the focused test**

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_required_structure -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .codex-plugin skills tests requirements-dev.txt .gitignore .gitattributes .editorconfig README.md LICENSE
git commit -m "feat(plugin): add SkipHow skeleton"
```

### Task 3: Port the canonical cto-run workflow

**Files:**
- Modify: `skills/cto-run/SKILL.md`
- Create: `skills/cto-run/references/operating-policy.md`
- Create: `skills/cto-run/references/state-contract.md`
- Create: `skills/cto-run/references/capability-routing.md`
- Create: `skills/cto-run/references/host-notes.md`
- Create: `skills/cto-run/assets/runbook-template.md`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: a user invocation with `runbook`, `run directory`, and optional `target`.
- Produces: the durable paths `state.json`, `journal.jsonl`, `briefing.md`, `FINAL.md`, `decisions/`, `evidence/`, and `receipts/`.

- [ ] **Step 1: Add failing policy tests**

Add tests that assert:

```python
CAPABILITY_ROLES = {"MECHANICAL", "IMPLEMENTATION", "CTO_REVIEW"}
DURABLE_FILES = {"state.json", "journal.jsonl", "briefing.md", "FINAL.md"}
FORBIDDEN_TEXT = {
    "/Users/",
    "~/.codex",
    "~/.claude",
    "run-journal",
    "launch.sh",
    "gpt-",
    "opus",
    "sonnet",
    "haiku",
}
```

The tests read every shipped skill, reference, and asset. They require all capability roles and durable files, require a host-policy priority clause, and reject every forbidden string.

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_portable_policy -v
```

Expected: FAIL because the packaged policy does not exist.

- [ ] **Step 2: Write the skill entrypoint**

Keep `SKILL.md` short. It must resolve arguments, load the four references, load repository instructions, establish durable state, reconstruct current state, run the control loop, resume after context loss, and stop only at the runbook terminal condition or an authorized blocker.

The description must trigger only when the user explicitly names `cto-run`, supplies a runbook, or asks to resume an existing CTO run.

- [ ] **Step 3: Port the operating policy**

Extract the portable rules from the existing local policy. Preserve authority order, state recovery, risk classification, build-versus-reuse decisions, bounded delegation, circuit breakers, validation, independent review, exact-commit evidence, scope control, and terminal reconciliation.

Remove launcher rendering, model names, local binaries, personal directories, provider-specific compaction language, and hook assumptions. Route provider mechanics through `host-notes.md`.

- [ ] **Step 4: Add the state contract and template**

Define the JSON fields for current target, repository commit, active lanes, blocked lanes, decisions, evidence, and last reconciliation. Define journal events as JSON Lines with `at`, `task`, `event`, `status`, `summary`, and optional `evidence`.

The runbook template must include mission, coordinates, non-goals, protected actions, terminal condition, durable paths, dependency edges, recovery seed, outage fallback, and final handoff fields.

- [ ] **Step 5: Run the focused tests**

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_portable_policy -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add skills/cto-run tests/test_repository.py
git commit -m "feat(cto-run): port the orchestration workflow"
```

### Task 4: Add native Codex and Claude Code packaging

**Files:**
- Modify: `.codex-plugin/plugin.json`
- Create: `.agents/plugins/marketplace.json`
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `adapters/claude/skills/cto-run/SKILL.md`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: canonical workflow at `skills/cto-run/SKILL.md` and version `0.1.0`.
- Produces: installable Codex marketplace `skiphow` and Claude marketplace `skiphow`.

- [ ] **Step 1: Add failing packaging tests**

Add `test_manifest_contract`, `test_versions_match`, and `test_claude_adapter`. Require both manifests and both marketplace files to identify `skiphow`, require every version to equal `0.1.0`, require repository and license metadata, and require the Claude adapter to contain:

```yaml
disable-model-invocation: true
```

Also require the adapter body to point to `skills/cto-run/SKILL.md` and forbid it from containing the portable policy headings.

Run:

```bash
python -m unittest \
  tests.test_repository.RepositoryContractTests.test_manifest_contract \
  tests.test_repository.RepositoryContractTests.test_versions_match \
  tests.test_repository.RepositoryContractTests.test_claude_adapter -v
```

Expected: FAIL because Claude packaging does not exist.

- [ ] **Step 2: Complete the Codex package**

Fill the Codex manifest with author, homepage, repository, license, keywords, skills path, interface copy, three starter prompts, and no hooks, apps, or MCP fields. Point the repo marketplace source at the plugin root and set installation to `AVAILABLE`, authentication to `ON_INSTALL`, and category to `Developer Tools`.

- [ ] **Step 3: Add the Claude package**

Set the Claude manifest `skills` path to `./adapters/claude/skills/cto-run`. Create the public marketplace with GitHub source `mzored/SkipHow`. The adapter must be explicit-only and instruct Claude Code to load the canonical entrypoint and all references relative to the plugin root before executing.

- [ ] **Step 4: Run focused and official validators**

Run:

```bash
python -m unittest \
  tests.test_repository.RepositoryContractTests.test_manifest_contract \
  tests.test_repository.RepositoryContractTests.test_versions_match \
  tests.test_repository.RepositoryContractTests.test_claude_adapter -v
claude plugin validate .
```

Run the bundled OpenAI skill validator on `skills/cto-run` and plugin validator on the repository root. Expected: all commands pass.

- [ ] **Step 5: Commit**

```bash
git add .agents .claude-plugin .codex-plugin adapters tests/test_repository.py
git commit -m "feat(plugin): package Codex and Claude Code adapters"
```

### Task 5: Write public documentation and repository policy

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/skill_request.yml`
- Create: `.github/pull_request_template.md`
- Create: `.github/dependabot.yml`
- Create: `.github/workflows/ci.yml`
- Modify: `tests/test_repository.py`

**Interfaces:**
- Consumes: final install commands and plugin behavior.
- Produces: maintainer and user documentation for installation, invocation, contribution, security, and releases.

- [ ] **Step 1: Add failing documentation tests**

Require README sections for Codex, Claude Code, `cto-run`, support policy, limitations, contributing, security, and license. Require relative links to every public policy file. Require CI to run `python -m unittest discover -s tests -v` after installing `requirements-dev.txt`.

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_documentation_contract -v
```

Expected: FAIL because the complete documentation does not exist.

- [ ] **Step 2: Write the README and architecture guide**

Start with what SkipHow contains, then show verified install commands for Codex and Claude Code. Include one invocation example with a repository runbook and durable directory. Explain explicit invocation, host requirements, clean uninstall, and the absence of telemetry and MCP.

Document the canonical skill, Claude adapter, capability roles, durable files, and release gates in `docs/architecture.md`.

- [ ] **Step 3: Add repository policies**

Use the Contributor Covenant 2.1 text for `CODE_OF_CONDUCT.md`. Set private vulnerability reporting through GitHub Security Advisories in `SECURITY.md`. Keep `CONTRIBUTING.md` focused on one issue per change, tests, skill scope, host support evidence, and `unslop` for repository text.

Set `AGENTS.md` to require current primary documentation, tests before claims, no personal paths, one canonical workflow, and Codex plus Claude Code validation for changes that affect packaging or `cto-run`.

- [ ] **Step 4: Add CI and templates**

Create a single CI job on Ubuntu with Python 3.11. Install `requirements-dev.txt`, then run the unittest suite and `git diff --check`. Configure Dependabot for weekly pip and GitHub Actions updates.

- [ ] **Step 5: Run the focused test**

Run:

```bash
python -m unittest tests.test_repository.RepositoryContractTests.test_documentation_contract -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/architecture.md AGENTS.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md CHANGELOG.md .github tests/test_repository.py
git commit -m "docs: publish SkipHow contributor guide"
```

### Task 6: Verify, review, merge, and release 0.1.0

**Files:**
- Modify only when a validator or reviewer identifies a concrete defect.

**Interfaces:**
- Consumes: complete issue branch and exact base and head SHAs.
- Produces: merged issue `#1`, tag `v0.1.0`, GitHub release, and verified public installation instructions.

- [ ] **Step 1: Run the deterministic gate**

Run:

```bash
python -m unittest discover -s tests -v
git diff --check main...HEAD
```

Run the bundled OpenAI skill and plugin validators and `claude plugin validate .`. Scan tracked files for personal absolute paths, unfinished placeholders, em dashes, and stale versions. Expected: every command exits zero.

- [ ] **Step 2: Test clean local installation**

Create temporary home directories with `mktemp -d`. Install the Codex marketplace and plugin into one isolated profile. Add the Claude marketplace and install the plugin into the other isolated profile. Verify each host lists `skiphow`, exposes `cto-run`, and does not implicitly activate it for an unrelated prompt. Remove the temporary directories after recording commands and output under `docs/release-evidence/v0.1.0.md`.

- [ ] **Step 3: Request independent review**

Dispatch a fresh no-history `CTO_REVIEW` subagent with the exact `main...HEAD` diff, spec, plan, and verification output. Fix every critical or important issue after checking it against the repository. Rerun the affected tests after each fix and rerun the full gate if the diff changes.

- [ ] **Step 4: Merge and verify issue state**

Merge the issue branch into `main` with:

```text
feat(plugin): publish SkipHow 0.1.0

Closes #1
```

Push `main`, run `gh-task-status verify 1`, and add a comment with the merge SHA.

- [ ] **Step 5: Publish the release**

Create annotated tag `v0.1.0`, push it, and create a GitHub release from the `CHANGELOG.md` entry. Verify the tag targets the tested merge commit and the public repository exposes the release.

- [ ] **Step 6: Verify public installation paths**

Fetch the repository through its public GitHub URL into a fresh temporary directory. Repeat both marketplace validators against that clone. Confirm the README commands match the released manifests and tag.
