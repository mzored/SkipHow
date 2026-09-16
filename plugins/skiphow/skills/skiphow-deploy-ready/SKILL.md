---
name: skiphow-deploy-ready
description: Prepare agreed changes for delivery with deferred checks, review, commits, and authorized integration. Use for deploy-ready, release preparation, or clean at the end of an iteration session. Also carry an explicitly authorized deploy prod through verified release; preparation alone grants no production action.
---

# SkipHow deploy-ready

Prepare the agreed change set for delivery, and complete any delivery destination the owner has authorized. Before consequential work, have the [SkipHow CTO kernel](../skiphow/SKILL.md) in context. Read it if absent. Its authority and protected-action rules govern preparation and release.

The names deploy-ready and clean end an iteration session and request preparation. In this context clean is not permission to delete arbitrary work. A request to deploy prod additionally authorizes the specified production release within its stated scope. Honor an applicable earlier grant without asking again; preparation alone supplies none.

Recover the agreed changes, owned and foreign state, existing evidence, and delivery path. Use [verification](../skiphow/references/verification.md) to run the checks deferred during iteration and the checks required for this change and destination. Obtain review at the depth the kernel requires, resolve qualifying defects, and make coherent commits containing only owned changes through the permitted commit path.

Use [integration](../skiphow/references/integration.md) to complete an authorized non-production destination. Discover branches, release conventions, and downstream CI effects from the project. If a push, merge, or tag would cause an ungranted production effect, complete safe preparation and report that exact remaining action.

For an authorized production release, use [operations](../skiphow/references/operations.md) for readiness, migration and recovery needs, and operational evidence. Follow the project's release path, verify what actually reached production, and retire only owned resources that are no longer needed. A failed deployment remains a failure to diagnose and recover within the applicable grant.

Report the prepared or delivered revision, applicable checks and review, the verified destination, and any deferred action or cleanup blocker. Keep preparation, integration, and production status distinct.
