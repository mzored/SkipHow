---
name: skiphow-deploy-ready
description: Prepare agreed changes for delivery with deferred checks, review, commits, and authorized integration. Use for deploy-ready, release preparation, or clean at the end of an iteration session. Also carry an explicitly authorized deploy prod through verified release; preparation alone grants no production action.
---

# SkipHow deploy-ready

Prepare the agreed change set for delivery, and complete any delivery destination the owner has authorized. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. Its authority and protected-action rules govern preparation and release.

The names deploy-ready and clean end an iteration session and request preparation. In this context clean is not permission to delete arbitrary work. A request to deploy prod additionally authorizes the specified production release within its stated scope. Honor an applicable earlier grant without asking again; preparation alone supplies none.

Recover the requested delivery set, this session's state and what other sessions left, existing evidence, and delivery path. Reconcile running assignments, shown results, pending feedback, and cancellations so in-flight requested work is not silently omitted. Finish independent ready work in that set and preserve concrete blockers under [tracked work](../skiphow/references/tracked-work.md); a blocked remainder is not delivered. New messages may revise this delivery or add later work. Retain both, asking only when that distinction leaves a material product choice unresolved.

Use [verification](../skiphow/references/verification.md) to run the checks deferred during iteration and those required for this change and destination. Obtain risk-scaled review, resolve qualifying defects, and make coherent commits containing only owned changes through the permitted commit path. Bind acceptance and publication to the actual candidate: a late return or correction enters it only after review and affected revalidation. Unrelated additions do not silently enlarge the candidate or lose their place in accepted work.

Use [integration](../skiphow/references/integration.md) to complete an authorized non-production destination. Discover branches, release conventions, and downstream CI effects from the project. If a push, merge, or tag would cause an ungranted production effect, complete safe preparation and report that exact remaining action.

For an authorized production release, use [operations](../skiphow/references/operations.md) for readiness, migration and recovery needs, and operational evidence. Follow the project's release path, verify what actually reached production, and retire only owned resources that are no longer needed. A failed deployment remains a failure to diagnose and recover within the applicable grant.

Report the prepared or delivered revision, applicable checks and review, the verified destination, and any deferred action or cleanup blocker. Keep preparation, integration, and production status distinct.
