# Architecture decisions

This directory records accepted SkipHow architecture decisions. [How it works](../how-it-works.md) describes the current design. The [1.0 research](../research/2026-08-26/README.md) records the latest release evidence. The [2026-08-25 research](../research/2026-08-25/README.md) records the host-native rewrite that preceded it.

An accepted decision stays in place until a later ADR replaces it. Correct factual errors and broken links in place, but do not rewrite the decision to hide an architectural change.

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-one-owner-entry.md) | Use one owner-facing SkipHow skill | Accepted |
| [0002](0002-host-native-execution.md) | Use host-native execution | Accepted |
| [0003](0003-semantic-model-routing.md) | Route models by semantic capability | Accepted |
| [0004](0004-github-lifecycle-and-authority.md) | Define GitHub lifecycle and authority | Accepted |
| [0005](0005-fail-closed-release-evaluation.md) | Keep release evaluation repository-free and fail closed | Superseded by 0008 (claims policy stands) |
| [0006](0006-host-native-campaign-and-engineering-policy.md) | Keep campaign and engineering policy host-native | Accepted |
| [0007](0007-host-adapters-for-routing-and-continuity.md) | Resolve model tiers and session continuity in host adapters | Accepted |
| [0008](0008-receipts-over-a-live-harness.md) | Prove model behavior with receipts, not a live harness | Accepted |
