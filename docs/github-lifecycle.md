# GitHub lifecycle

GitHub delivery is optional. It applies only when tracked lifecycle work is needed by the request, an existing Issue, or repository policy. An Issue is the canonical work identity. A GitHub Project is an optional view, never lifecycle authority.

## Contract

The controller decides scope, priority, readiness, review depth, and whether delivery needs a campaign. The GitHub adapter reconciles remote state and performs authorized operations. Repeating a run must not create a duplicate Issue, branch, pull request, delivery comment, merge, or deletion.

The ready queue derives from Issue state, native dependencies and sub-issues, repository policy, active leases, branch and pull request state, required checks, and owner priority. SkipHow does not scan Projects to infer readiness.

Independent mutable lanes use separate system-owned branches and worktrees, with one writer per owned scope. Metadata links each branch to its run, task, and Issue. A sequential task does not require a worktree. User branches, dirty worktrees, and unrelated changes remain untouched.

A pull request covers one coherent deliverable. It links its Issue and uses `Closes #N` only when the merge completes that item. Its description states the outcome, verification, and material limits. Completion evidence must match the exact head commit.

The controller waits for required checks and reviews, classifies failures, fixes failures caused by its change, and reruns only invalidated checks. Independent work may continue during an external wait.

Merge policy is `never`, `when_green`, `when_green_and_approved`, or `auto_merge_or_queue`. The default is `never` unless repository policy says otherwise. A merge requires explicit authority, satisfied protections, green required checks, required approval, no unresolved blocking finding, and evidence for the exact head.

After a confirmed merge, cleanup may remove a clean system-owned worktree and a merged system-owned branch with no unique commits. It may stop owned processes, close leases, prune stale metadata, update the Issue and configured Project view, and retain final references. It never deletes an unmerged branch, unique commits, user state, or a resource whose ownership is uncertain.

## Current implementation status

The GitHub helper implements bounded Issue candidates, operation-ID Issue reconciliation, updates, keyed provenance, native relationships with a feature-detected fallback, owned worktrees, pull request reconciliation, exact-head checks and reviews, merge-policy gates, and guarded remote and local cleanup. The adapter does not own product or engineering decisions.

`skiphow github-deliver` is the durable campaign delivery path. It accepts one operation ID, task, repository, Issue, branch, expected 40-character head, owner, title, body, required checks, base, and an explicit green merge policy. Before remote access it requires an active run, a completed task, and exact matching authority for repository, Issue, branch, owner, base, head, checks, merge, cleanup, and protected-branch action. A process lock serializes the operation for that runner database.

Each invocation reconciles an owned pull request by its operation marker, refuses duplicates or identity drift, and persists the delivery phase. It returns `WAITING_EXTERNAL` while CI, mergeability, approval, merge, or Issue closure is pending. Completion requires the exact head in the default branch, closure of the Issue by that pull request, absence of the owned remote branch, and a durable receipt. Replaying a completed operation revalidates those remote facts. Cleanup uses exact origin and ownership metadata with force-with-lease.

Deterministic tests exercise idempotent commands and refusal paths without a network. `scripts/check_github_e2e.py` adds the real remote gate. It uses one explicitly configured private sandbox, creates signal and delivery Issues with a native blocking dependency, opens a pull request from a run-unique branch, waits for CI on the exact head, merges, verifies Issue closure and the default branch, and removes the merged delivery branch. The receipt grades against `evals/scenarios/github-lifecycle.json`.

The harness never creates or deletes a repository. A human or separately governed provisioning workflow must supply the sandbox. The sandbox must:

- differ from the candidate repository;
- be private, unarchived, use `main` as its default branch, and have Issues enabled;
- have the exact description `skiphow-github-e2e-sandbox`;
- contain `.skiphow-e2e-sandbox.json` with `{"schema_version": 1, "purpose": "skiphow-github-e2e-sandbox"}`;
- contain `.github/workflows/e2e.yml` with a noninteractive `pull_request` check.

The workflow fixture is exact so the gate cannot execute arbitrary sandbox code:

```yaml
name: SkipHow E2E
on:
  pull_request:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Verify event
        run: test -n "$GITHUB_SHA"
```

Give the gate credentials access only to this sandbox. The required repository permissions are Contents, Issues, and Pull requests write access plus Checks read access. Do not grant repository creation, repository deletion, or organization-wide access. The harness binds state to GitHub's stable numeric repository ID, refuses the candidate repository, verifies the exact inert workflow fixture, and refuses a new run while another `skiphow/e2e-` branch exists. Closed Issues and merged pull requests remain as the sandbox's audit history.

The first invocation must inject an exit after `issues`, `pull_request`, or `ci_success`. The second invocation uses the persisted state and `--resume`. For example:

```sh
E2E_DIR="$(mktemp -d)"
SKIPHOW_GITHUB_E2E=1 python scripts/check_github_e2e.py \
  --state "$E2E_DIR/state.json" \
  --repo GITHUB_OWNER/GITHUB_E2E_SANDBOX \
  --crash-after ci_success \
  --live

SKIPHOW_GITHUB_E2E=1 python scripts/check_github_e2e.py \
  --state "$E2E_DIR/state.json" \
  --resume \
  --live
```

The first command exits with code 75 after persisting the selected phase. The resumed command writes a receipt outside the candidate repository. A successful run removes its merged delivery branch. It closes its two Issues through the tested lifecycle and leaves their immutable history for inspection.

This gate requires a clean committed candidate, authenticated `gh`, sandbox-scoped remote mutation authority, and native Issue relationship support. It is separate from `scripts/check.py`. It supplies one real-service collector for the broader multi-trial provider and service evidence that remains `UNVERIFIED` for the release candidate. Project synchronization is outside the canonical Issue operation and is not a completion requirement.
