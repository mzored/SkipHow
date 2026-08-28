# Decision history

This page records the choices that still matter when SkipHow changes. Read it before reopening an old design argument.

The complete decision archive remains available in the immutable [`v2.0.1` source snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/decisions). The matching [research and receipts](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research) preserve the full evidence behind the summaries below.

## One owner entry

SkipHow exposes one plain-language skill. Focused methods remain internal references.

Earlier versions tried named routes, separate commands, role files, and sibling method skills. Those shapes either exposed engineering workflow to the owner or allowed a method to load without the authority kernel.

Revisit this if a portable skill standard adds required skill dependencies, or repeated receipts show one entry causing missed outcomes or unauthorized actions.

## Host-native execution

SkipHow relies on host sessions, worktrees, subagents, permissions, and continuation. It does not ship a runner or coordinator.

The project built and removed Python runtime machinery. It duplicated host state, increased failure modes, and made a small instruction package responsible for orchestration.

Revisit this if supported hosts lose required durability, or verified demand appears for provider-neutral unattended work on hosts without native continuation.

## Authority follows the requested outcome

Read-only requests stay read-only. Record requests grant only the record. Project changes include edits, checks, and a clean local commit. Shared delivery must be requested. Protected actions need an explicit grant.

Earlier versions tried magic phrases, fixed routes, tracker markers, and GitHub lifecycle rules. They made wording and procedure more important than the owner's actual outcome.

Revisit this if a receipt shows an unauthorized protected action, a dropped material outcome, or repeated questions about routine engineering mechanics.

## No universal engineering workflow

Planning, TDD, review, worktrees, delegation, and pull requests are tools. None is a mandatory stage for every request.

The 1.x contract accumulated planner, builder, reviewer, model tier, queue, timeout, diff, and prose rules. The root grew while small work still stalled on mechanics. Version 2.0 removed those gates.

Reconsider one method only when paired evidence shows that it adds cost or delay without improving the result. Add a universal rule only when capable agents repeatedly miss a high-risk boundary without it.

## Critical rules stay in the kernel

Authority, autonomy, preservation, and completion remain in `SKILL.md`. Conditional technique belongs in a focused reference.

Earlier designs put mandatory behavior behind conditional reads. Missing one reference could change what the agent was allowed or required to do.

Revisit this if a critical rule moves behind a reference, or installed receipts repeatedly miss a method needed for correct work.

## Provider-independent policy

The shared skill contains no versioned provider model IDs, cost tables, or host-specific routing tiers. Hosts choose models and effort.

Several releases tried semantic tiers and adapter files. Host metadata changed too quickly, and the package had no reliable cost signal for a portable router.

Revisit this if hosts publish a stable portable capability interface and paired runs show a material quality or total-cost benefit.

## Receipts prove model behavior

Deterministic checks prove package structure. They do not prove how a model behaves. Deliberate runs with retained receipts support behavior claims.

The project removed a live evaluation harness because it could mutate repositories, spend budget, and still fail to prove the exact installed package. A later contributor-only transcript parser became larger than the product and coupled maintenance to private host log formats. Version 2.0.2 removes that parser from the repository.

Revisit automated evaluation when a host offers repository-preserving runs against an exact installed package with trustworthy receipts.

## Keep the current tree current

Current design, decisions, and evidence stay in four small documents. Superseded raw material remains in immutable commits, tags, pull requests, and releases.

Do not add one ADR or research file per release. Update this page when a decision changes. Update [`evidence.md`](evidence.md) when the set of supported claims changes. Link to durable source material instead of copying it into the current tree.
