---
name: skiphow-deploy-ready
description: Prepare agreed changes for delivery with deferred checks, review, commits, and authorized integration. Use for deploy-ready, release preparation, or clean at the end of an iteration session. Also carry an explicitly authorized deploy prod through verified release; preparation alone grants no production action. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow deploy-ready

Prepare the agreed change set for delivery, and complete any destination the owner has authorized. Before consequential work, and again after any context compaction, load the [SkipHow CTO kernel](../skiphow/SKILL.md) by invoking the `skiphow` skill where the host has a skill tool, otherwise by reading it, unless its full text is already in context; a summary is not its text. Its authority and protected-action rules govern preparation and release.

## What the request grants

Deploy-ready and clean end an iteration session and ask for preparation. Here clean is not permission to delete arbitrary work. Deploy prod also authorizes the named production release within its stated scope. Honor an applicable earlier grant without asking again; preparation alone supplies none.

## The delivery set

Recover the requested set, this session's state, what other sessions left, existing check results, and the delivery path. Reconcile running assignments, shown results, pending feedback, and cancellations so in-flight requested work is not dropped without a word. Finish independent ready work in the set and keep concrete blockers under [tracked work](../skiphow/references/tracked-work.md); a blocked remainder is not delivered. New messages may revise this delivery or add later work. Keep both, and ask only when telling them apart leaves a material product choice open.

## Preparing the candidate

Run the checks deferred during iteration and those this change and destination need, reusing passing results for the same command, tree, and environment, as [testing](../skiphow/references/testing.md) describes. Review at the depth the change warrants under [review](../skiphow/references/review.md) and fix what qualifies. Remove plan, report, and analysis files the work left in the repository. Make coherent commits of owned changes through the permitted commit path.

Bind acceptance and publication to the actual candidate. A late return or correction enters it only after review and a recheck of what it affects. Unrelated additions do not enlarge the candidate, and they keep their place in accepted work.

## Delivery

Use [integration](../skiphow/references/integration.md) to reach an authorized non-production destination. Read branches, release conventions, and downstream CI effects from the project. If a push, merge, or tag would cause a production effect nobody granted, finish the safe preparation and report that exact remaining action.

For an authorized production release, check readiness, migration, and rollback as [review](../skiphow/references/review.md#security-reliability-and-operations) describes, and follow the project's release path through integration. Verify what actually reached production, and retire only owned resources that are no longer needed. A failed deployment stays a failure to diagnose and recover within the applicable grant.

Report the prepared or delivered revision, the checks and review it got, the verified destination, and any deferred action or cleanup blocker. Keep preparation, integration, and production status distinct.
