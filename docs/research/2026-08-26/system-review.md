# System review of SkipHow 1.0.1

## Record

- Reviewed on 2026-08-26 at `main` commit `9d9aa71`.
- Inputs: the packaged skill and references, all ADRs and docs, `scripts/`, `tests/`, `evals/`, the two dated research directories, `python scripts/check.py` (pass), `python scripts/check_hosts.py` (Claude pass, Codex `UNVERIFIED` locally because the validator is fetched only in CI), and the [host](host-routing-and-continuity.md) and [prior-art](prior-art-mechanics.md) research from the same day.
- Question: does the current design do what the owner wants, and where does it work against itself?

## What the owner wants

One plain-language entry point. Routine choices made by the agent. Small requests finished in the current session with no ceremony. Large requests (an epic, a night of Issues) run through subagents to the end, tracked in GitHub, cleaned up afterwards, and recoverable after compaction. Cheap models for search, stronger ones for code, the strongest for planning and review, without pinning any provider's model names. Findings outside the task saved, not swallowed. Existing solutions reused instead of rebuilt. Little documentation to read.

## What already works

The architecture is right. One skill, four internal routes, authority from the owner's words, GitHub as the only tracker, host-native execution, no runner. The retired Python runner would have fought both hosts forever. ADRs 0001, 0002, and 0004 hold up against the fresh host research and should stay.

The deterministic checks are solid. Version alignment, link checking, budget, no personal paths, package validation in both hosts, SHA-pinned CI.

The authority model is better than every prior-art project reviewed. None of them separates "save" from "fix" from "finish end to end" this cleanly.

## Where it works against itself

### 1. Model routing is defined but inert

`references/model-routing.md` and ADR 0003 say the root maps tiers only from "capability, cost, or latency metadata exposed by the host" and otherwise inherits. Neither host exposes that metadata, and the plugin ships no agent definitions. So today every subagent runs on the owner's main model. The tiers are documentation. This is the single biggest gap against the owner's brief.

Both hosts do support per-agent model and effort (see the host research). Claude Code lets a plugin ship `agents/*.md` with `model: haiku|sonnet|opus` family aliases that the vendor calls stable. Codex has `.codex/agents/*.toml` and `[agents].default_subagent_model`, though a plugin cannot ship them. The fix is a small host adapter per host, kept out of the shared policy. ADR 0007 records it.

### 2. Compaction continuity is asked of the model, not provided by the host

`long-work.md` tells the root to checkpoint "before compaction". The model cannot see compaction coming. AGENTS.md, ADR 0002, `scripts/check.py`, and a test all forbid hooks, yet a `SessionStart` hook with the `compact` and `resume` matchers is the one mechanism both hosts document for putting text back into a resumed session. The prohibition made sense when hooks meant a private runtime. A two-line read-only hook that prints "read `.skiphow/handoff.md`" is not a runtime.

### 3. The policy has become the kind of framework it rejects

The prior-art note credits SkipHow with leaving out ceremony. Then `long-work.md` specifies a 23-field checkpoint with exact labels, a 15-line worker packet, `CIRCUIT_BROKEN` lanes, "compare-and-delete semantics", and "effective diff hash" evidence binding. `github.md` has a 13-step lifecycle. The references total about 5,400 words of dense legal prose on top of a 640-word root. Much of it was written to close audit findings rather than to help a strong model act. The owner's own philosophy, that detailed instructions to a strong model make results worse and slower, applies to this text.

The right size is roughly half. Keep the hard invariants (authority, never delete unmerged work, re-read live state before merge, name every selected item at the end). Replace procedure with intent everywhere else.

### 4. Tests freeze the prose

`tests/test_repository.py` asserts exact English sentences ("One quiet signal does not prove a stall", "A timer firing does not prove that a remote mutation failed"). Any rewrite of the references breaks tests that check wording, not behavior. Structural tests (routes present, references linked, budget, no versioned model IDs, no personal paths, manifests aligned) are worth keeping. Sentence assertions should go.

### 5. The owner's daily flow is possible but not obvious

The owner's pattern is: dump bugs and ideas, have them triaged and saved to GitHub, then start one run that finishes them overnight. The routes support this (`RECORD`, then `DELIVER` with "end to end"). Nothing makes it easy. The README leads with three unrelated examples. There is no way to say "finish today's batch" without listing Issue numbers, and no launch recipe for an unattended run on either host.

### 6. Documentation duplicates policy

`docs/intake.md`, `docs/github-lifecycle.md`, and `docs/model-routing.md` restate the references. `docs/architecture.md`, `docs/trust.md`, and `docs/threat-model.md` overlap. `docs/evals.md` is 1,460 words about a harness that has never produced a receipt. Around 26,000 words of docs for a tool whose pitch is "you do not need to read documentation".

### 7. Reuse-before-build is one paragraph

`delivery.md` has a good paragraph under "Prefer maintained code". It triggers on "framework, scheduler, storage layer, authentication layer, protocol, or lasting abstraction". It does not trigger on the common case: a feature that the project, a dependency, or the platform already provides in part. Matt Pocock's triage rule (search by domain concept, report where you looked) is the missing half.

### 8. Findings policy is thorough to the point of noise

Five triage labels in `delivery.md`, six dispositions in `intake.md`, four more in `review.md`. The rule the owner cares about is one sentence: fix it if it blocks you, save it once if it matters, say so in the report. Superpowers' "Rulings I made" section is the missing report element; the labels can shrink.

### 9. The live evaluator is large and has produced nothing

`evals/live/run.py` is 1,392 lines plus 728 lines of tests. The scenario that matters most (multi-Issue GitHub delivery) fails closed by design. No receipt has been published for any scenario. The harness is not wrong, but it is the wrong first investment. One real dogfooding run of the owner's daily flow, with a written receipt, would say more than the harness can.

### 10. Repository hygiene

`VERSION` is 1.0.1 but the latest tag and GitHub release are 1.0.0. Untracked leftovers from the runner era sit in the checkout (`build/lib/skiphow`, empty `src/`, empty `.worktrees/`, `evals/deterministic` and `evals/graders` containing only bytecode). `.gitignore` still lists `.skiphow/runs/` and `.skiphow/intake/`. `SECURITY.md` supports `1.0.x` only, so the next minor needs an update. There is no release workflow; releases are manual.

## Checks on the earlier agent's recommendations

The 1.0 and 1.0.1 audits were correct on their facts: repository policy must beat the small-change shortcut, privacy-boundary changes need a durable record, independent findings need triage, dirty overlap weakens attribution. The fixes were correct in direction and too heavy in form. Each added paragraphs of procedure and a matching sentence-level test. The recommendation to keep evaluating live model behavior separately from package checks stands.

The earlier model-routing research reached the right conclusion (tiers in policy, host resolves) and the wrong stopping point (wait for host metadata). Family aliases in a host adapter are the practical resolution and were available at the time.

## Recommendation

Ship 1.1 as a consolidation release: real routing through host adapters, continuity hooks, references cut to intent plus invariants, structural tests only, one owner guide, a README that leads with the daily flow, cleanup of leftovers, and a tag-driven release workflow. Then dogfood the daily flow on a real project and publish the first receipt. Details are in the [1.1 brief](v1.1-brief.md) and [ADR 0007](../../decisions/0007-host-adapters-for-routing-and-continuity.md).
