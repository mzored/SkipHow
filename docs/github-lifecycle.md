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

Deterministic tests exercise idempotent commands and refusal paths without a network. `scripts/check_github_e2e.py` adds the real remote gate. It creates an owned disposable private repository and a marker commit, creates signal and delivery Issues with a native blocking dependency, opens a pull request, waits for CI on the exact head, merges, verifies Issue closure and the default branch, and removes the merged delivery branch. The receipt grades against `evals/scenarios/github-lifecycle.json`.

The first invocation must inject an exit after `issues`, `pull_request`, or `ci_success`. The second invocation uses the persisted state and `--resume`. For example:

```sh
E2E_DIR="$(mktemp -d)"
SKIPHOW_GITHUB_E2E=1 python scripts/check_github_e2e.py \
  --state "$E2E_DIR/state.json" \
  --owner GITHUB_OWNER \
  --crash-after ci_success \
  --live

SKIPHOW_GITHUB_E2E=1 python scripts/check_github_e2e.py \
  --state "$E2E_DIR/state.json" \
  --resume \
  --live
```

The first command exits with code 75 after persisting the selected phase. The resumed command writes a receipt outside the candidate repository. The disposable repository remains for inspection. Deleting it requires `--cleanup` and an exact `--confirm-delete owner/repository` value.

This gate requires a clean committed candidate, authenticated `gh`, remote mutation authority, and an owner account allowed to create a private repository and native Issue relationships. It is separate from `scripts/check.py`. Until a receipt for the exact release candidate is retained and reviewed, the live GitHub gate is `UNVERIFIED`. Project synchronization may remain `UNVERIFIED` without invalidating an otherwise completed canonical Issue operation.
