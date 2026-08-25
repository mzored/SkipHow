# GitHub lifecycle

GitHub delivery is optional. Use it when the request names tracked work, the work already has an Issue, or repository policy requires it. Small local changes do not gain an Issue and pull request solely because they modify code.

For tracked work, Issues hold scope and relationships. Pull requests hold delivery and review state. Git records the exact code state. SkipHow does not maintain another task database.

A GitHub Project may display this work. It does not control readiness, dependencies, or completion.

## Lifecycle

For each tracked item, the agent:

1. finds or creates the Issue after searching open and closed work for duplicates;
2. reads parent, sub-issue, and dependency state;
3. records a stable operation marker for any object it may need to reconcile;
4. creates an owned branch and an isolated worktree when the host supports it;
5. implements the accepted scope and checks the final local state;
6. finds or creates one pull request for the coherent deliverable;
7. links the Issue with a closing keyword only when that pull request completes it;
8. records and rechecks the exact pull request head before protected actions;
9. waits for repository-required checks and reviews, then makes bounded repairs for failures caused by the change;
10. merges only with authority and satisfied repository rules;
11. confirms the merged state before closing the Issue or updating dependencies;
12. removes only the owned merged branch and clean worktree.

Remote mutations are serialized. Before a create, the agent records the intended stable marker and identity. It then calls GitHub and reads the observed result. A retry reconciles remote state before it creates or changes anything. External APIs do not promise exactly-once creation, so SkipHow promises reconciliation, not exactly-once delivery.

Independent write tasks use separate worktrees and branches. The root agent owns integration. If safe isolation is unavailable, serialize repository writes.

## Merge authority

"Fix", "implement", and "deliver" permit work through a ready pull request when the repository uses one. They do not grant merge by implication.

"Finish end to end", "run unattended", "complete these Issues", or equivalent wording grants guarded merge and cleanup for the named scope. "Do not merge" removes that authority immediately.

A merge requires all of these facts:

- the Issue belongs to the authorized scope;
- the pull request head still matches the checked commit;
- required checks and reviews have an accepted result;
- no blocking finding remains unresolved;
- branch protection, rulesets, and the merge queue allow the action;
- the chosen merge method follows repository policy.

SkipHow never uses an admin or protection-bypass option. It does not change repository settings to make a merge pass. After the request, it re-reads the pull request and requires GitHub to report the merge before it treats delivery as complete.

Production deployment, payments, credentials, privacy operations, public release, repository settings, and irreversible remote deletion need their own exact grant. End-to-end code delivery does not include them.

## Cleanup

Cleanup runs only after GitHub confirms `mergedAt` for the recorded pull-request head. The branch must belong to this operation, have no other open pull request, and contain no work omitted from the confirmed merge. For squash or rebase, compare the recorded head and merged result instead of requiring commit ancestry. The worktree must be clean.

If any fact is missing, leave the branch or worktree in place and report it. Never delete a user branch, dirty worktree, unmerged branch, unincorporated commit, or uncertain file.

## Resume and missing features

After compaction, pause, or restart, re-read the Issue, pull request, exact head, checks, reviews, Git state, and current authority before acting. Do not trust a transcript summary as current remote state.

Some repositories lack native dependency relationships, merge queues, or automatic branch deletion. Use the available GitHub state and report missing behavior as `UNVERIFIED`. Do not recreate those features in a local queue.

If GitHub is unavailable, an authorized record request may use `.skiphow/inbox.md`. That fallback does not provide a GitHub delivery lifecycle.

The full authority decision is in [ADR 0004](decisions/0004-github-lifecycle-and-authority.md). Live GitHub evidence must follow the [evaluation policy](evals.md).
