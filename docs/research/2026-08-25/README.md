# Architecture review from 2026-08-25

This directory preserves the evidence used for the current SkipHow architecture. Start with the topic that matches the change you are considering. Read the linked ADR before changing accepted policy.

| Topic | What it records |
| --- | --- |
| [Repository audit](repository-audit.md) | The audited code, tests, gaps, and removal decision |
| [Product and UX](product-and-ux.md) | The one-entry owner contract, intake, authority, progress, and controls |
| [Host capabilities](host-capabilities.md) | Current Codex and Claude execution, delegation, worktree, resume, and packaging facts |
| [Model routing](model-routing.md) | Audited router defects and the provider-neutral replacement policy |
| [Security and evals](security-and-evals.md) | Trust boundaries, evidence rules, and live evaluation limits |
| [Live evaluation hosts](live-evaluation-hosts.md) | Exact candidate loading, noninteractive host commands, budgets, events, and replacement-suite boundaries |
| [Release-readiness audit](release-readiness-audit.md) | Final semantic, packaging, security, and evidence corrections after the host-native rewrite |
| [Codex OAuth evaluation](codex-oauth-evaluation.md) | API-key-free live evaluation through the existing ChatGPT OAuth profile |
| [Prior art](prior-art.md) | Pinned reviews of GSD, OpenSpec, Superpowers, Matt Pocock skills, BMAD, Paperclip, Mesa, and Autonomous PM |

The review applies to repository commit `a6d34a25614bc0723517032af617b0782158df4d`. Later implementation work may remove the audited code. The findings remain useful because they explain why it was removed.

Facts that depend on a host, provider, GitHub API, or upstream project can expire. Each topic lists its own revalidation triggers. Update only the affected topic, then add or replace an ADR if the decision changes.

The accepted decisions are indexed in [Architecture decisions](../../decisions/README.md). The target design for Issue #15 is in [Architecture](../../architecture.md).
