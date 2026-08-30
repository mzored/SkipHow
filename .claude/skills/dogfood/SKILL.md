---
name: dogfood
description: Inspect the owner's Codex or Claude Code transcripts to explain SkipHow behavior, cost, or version effects and decide whether the evidence supports changing the package. For this repository only.
---

# Dogfood

Use real sessions to separate what SkipHow said from what the run did. Explain the observed behavior without
turning one transcript into a general theory of agents.

This is a contributor skill and does not ship. Do not invoke the `skiphow` skill while examining this
repository. The package is the subject of the investigation, not its authority.

## Locate the evidence

Search the owner's local transcripts for a distinctive excerpt from the session. Transcripts are private
JSONL files, usually one per root or subagent session. Host formats change, so inspect the records you find
instead of relying on a fixed parser. Prefer direct search and disposable extraction over a maintained tool
for these private, unstable formats.

Claude Code keeps sessions under the projects directory in its configuration home, with subagents in separate
files. For Codex, active rollouts are under `$CODEX_HOME/sessions/YYYY/MM/DD/`, or
`~/.codex/sessions/` when `CODEX_HOME` is unset. Archived rollouts are under the sibling
`archived_sessions/` directory. App task tools can identify the thread ID; the corresponding rollout
filename ends in that ID.

A Codex text search may match subagent rollouts because they inherit parent history. Use
`session_meta.payload.id`, `thread_source`, and
`source.subagent.thread_spawn.parent_thread_id` to distinguish the root and follow its descendants when
their work matters to the question.

Keep transcript contents out of delegate briefs and external output. Copy private material into a durable file
only when it is necessary and has been checked.

## Reconstruct the run

Read only as broadly as the question needs, but preserve the distinctions that determine the answer:

- Identify the package version that ran and compare against that version from git history, not the current
  tree.
- Establish what instruction text reached the agent. A path in a command or search result does not prove that
  the file's rules entered context; look for the wording itself.
- Recover the owner's actual requests across every input channel in the transcript, including later turns
  that changed scope or permission.
- Compare the actions and tool results with what the run reported.
- For cost or execution-health questions, use transcript timestamps and usage records and include relevant
  subagents rather than estimating from the visible conversation.

In current Codex rollouts, `session_meta` identifies the thread and lineage, `turn_context` records model
and execution settings, `response_item` holds messages and tool traffic, `event_msg` carries turn timing
and token counts, and `compacted` records context replacement. These are landmarks, not a stable schema.
App task summaries can locate a run, but the raw rollout is the evidence for exact context, actions, timing,
tokens, and subagent work.

## Judge the evidence

Distinguish three explanations:

- The package text was missing, ambiguous, contradictory, or unreachable. One session can demonstrate such a
  defect because the governing text and its context are inspectable.
- Plain wording reached context and the run departed from it. The transcript demonstrates that incident, not
  a general failure rate or a need for more procedure.
- The expectation does not match the contract. SkipHow may deliberately leave the choice to agent judgment,
  or the project may narrow the package's default.

Use `UNVERIFIED` when the transcript does not distinguish them. Count observations by whole session and pool
only sessions governed by the same package text. Several deviations within one session remain one
observation. Apparent conformance is an upper bound because a transcript cannot expose a finding the run never
reported or acted on.

## Change only what the evidence reaches

Design a package change only when the evidence identifies a defect in its wording or placement. A cost
measurement, an isolated departure from plain text, or an unresolved cause ends in a report rather than a
manufactured fix.

Check [`docs/decisions.md`](../../../docs/decisions.md) before reopening settled reasoning. Read
[`docs/prior-art.md`](../../../docs/prior-art.md) when a comparable mechanism would materially inform the
fix, not as a standing research step. Prefer the smallest correction that removes the defect. Consider whether
the text will reach the requests it governs and what instruction cost it adds to future runs. One session may
prove that wording is broken; it does not prove that agents generally need a new step, gate, or workflow.

Report the reconstructed facts, the conclusion they support, and what remains uncertain. If the owner asked
for a change, implement the justified correction under the repository's contributor rules.
