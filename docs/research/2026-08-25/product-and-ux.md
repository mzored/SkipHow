# Product and UX research

## Review record

- Reviewed on 2026-08-25.
- Repository commit: `a6d34a25614bc0723517032af617b0782158df4d`.
- Local hosts available during review: Codex CLI `0.149.1` and Claude Code `2.1.240`.
- Scope: the public entry point, natural-language use, intake, authority, progress, and controls.
- This note records product decisions and the facts behind them. It is not a transcript.

## Verified facts

Agent Skills already provide the discovery mechanism SkipHow needs.

- ChatGPT and Codex start with a skill's name and description, then load its body when needed. They can select a skill from the task or accept an explicit mention. In Codex CLI and the IDE, the explicit form is `$skiphow`. See [OpenAI's skill guide](https://learn.chatgpt.com/docs/build-skills).
- Claude Code also selects skills by description. A plugin skill has a namespaced explicit form, so this plugin appears as `/skiphow:skiphow`. See [Anthropic's skill guide](https://code.claude.com/docs/en/slash-commands) and [plugin guide](https://code.claude.com/docs/en/plugins).
- Both hosts therefore support normal requests such as "fix the checkout bug" without requiring a separate command for each intent. Explicit invocation remains useful when automatic matching fails.
- OpenAI advises long-running work to name the outcome, constraints, and proof of completion. The same chat can accept status questions and new constraints while a goal runs. See [OpenAI's long-running work guide](https://learn.chatgpt.com/docs/long-running-work).
- Claude Goal mode reports its condition, elapsed time, evaluated turns, token spend, and the evaluator's latest reason. See [Anthropic's Goal mode guide](https://code.claude.com/docs/en/goal).

These facts support one entry point. They do not prove that either host will classify every SkipHow request correctly. Exact invocation and outcome behavior still need package and live tests.

## Verification record

The following non-mutating checks ran on 2026-08-25 in a worktree at repository commit `b679bbb923bce1865fa9b130d74d811e55187ba9`:

```bash
python -m json.tool plugins/skiphow/.codex-plugin/plugin.json
python -m json.tool plugins/skiphow/.claude-plugin/plugin.json
claude plugin validate plugins/skiphow
find plugins/skiphow -name SKILL.md -type f -print
rg -n '^name: skiphow$|^description:' plugins/skiphow/skills/skiphow/SKILL.md
```

Observed results:

- Both manifests parsed as JSON. Each used the plugin name `skiphow`, version `0.9.0`, and `skills` path `./skills/`.
- `claude plugin validate plugins/skiphow` reported `Validation passed`.
- The file search returned one `SKILL.md`, at `plugins/skiphow/skills/skiphow/SKILL.md`.
- The skill name was `skiphow`. Its description named product and project work, answers, research, ideas, intake, decisions, fixes, features, tracked delivery, and control.

No Codex candidate installation or host session ran during these checks. Codex plugin loading, Claude plugin loading, implicit selection, explicit invocation, route choice, batch intake, authority handling, and natural-language controls remain `UNVERIFIED` by this record. Those behaviors need package installation checks and opt-in live runs against the exact candidate.

## Product decision

SkipHow has one public capability named `skiphow`. The owner describes the result in ordinary language. SkipHow decides how much process the work needs.

The product must not expose `/fix`, `/idea`, `/cto`, or `/automode`. Those names make the owner choose an internal workflow before the system has inspected the request. They also create overlapping contracts. A bug may need product clarification. An idea may be a two-line change. The routing belongs inside the skill.

Four internal routes are enough:

| Route | Owner intent | Default effect |
| --- | --- | --- |
| `RESPOND` | Discuss, explain, assess, or research | Read-only response |
| `RECORD` | Save ideas, bugs, questions, or decisions | Persist work items, but do not implement them |
| `DELIVER` | Fix, add, change, or finish work | Change the product and verify the result |
| `CONTROL` | Ask for status, pause, resume, narrow, or cancel | Apply the host's native control when available |

Bug repair is part of `DELIVER`. Long-running work is an execution choice, not a fifth owner command.

## Owner-facing contract

The following requests should work without the owner learning the route names:

```text
Add this function.
Find the display bug and fix it.
Save these ideas and bugs in GitHub.
Could error logging be clearer here?
Finish the ready Issues end to end.
Show me the current status.
Pause the work.
Continue, but do not merge.
```

Invocation differs by host:

- In Codex, the owner can write the request normally or prefix it with `$skiphow`.
- In Claude Code, the owner can write the request normally or use `/skiphow:skiphow`.
- README examples should lead with normal requests. Put explicit syntax in a short installation note.

The description in `SKILL.md` must mention product discussion, intake, bug repair, feature delivery, tracked work, and status control. Those words are part of the matching contract. The body can stay short and tell the host which reference to load after activation.

## Authority rules

Words grant different authority. SkipHow must keep these differences visible.

- "Discuss", "assess", and "research" authorize inspection only.
- "Save" and "create Issues" authorize persistence. They do not authorize implementation.
- "Fix", "implement", and "deliver" authorize repository changes and proportionate verification.
- "Finish end to end", "run overnight", and "complete the ready Issues" authorize unattended delivery, including merge and cleanup when repository rules allow both.
- "Do not merge", "stop at PR", "pause", and "cancel" narrow earlier authority immediately.

The owner chooses product behavior, scope, priority, privacy, spending, production changes, and irreversible external actions. SkipHow owns libraries, code structure, tests, model choice, subagent use, branches, and other engineering details unless one of those choices changes the product trade-off.

An unattended grant never bypasses repository protection, permissions, required review, required checks, or an exact-head check. It also never authorizes deletion of dirty worktrees, unmerged branches, unique commits, or work owned by another actor.

## Batch intake

The common intake request is a loose mix of observations, ideas, bugs, and questions. Do not make the owner rewrite it as tickets.

Process the batch in this order:

1. Preserve the original text and its source.
2. Split it into atomic signals without inventing facts.
3. Search existing work before creating anything.
4. Classify each signal as `NEW`, `UPDATE`, `DUPLICATE`, `RELATED`, or `NEEDS_RESEARCH`.
5. Merge signals only when evidence shows they describe the same requested outcome.
6. Return counts and links in a short summary.

When GitHub is connected, Issues are the source of truth. Without GitHub, append to `.skiphow/inbox.md`. Each entry needs a stable ID, timestamp, source text, normalized work item, and disposition. Do not create a second JSON queue or a private task database.

Intake stops after persistence. It does not start delivery unless the owner also asks to implement the resulting work.

## Progress and control

SkipHow should speak at decision boundaries, not narrate every tool call.

- At start, state the interpreted outcome and any material boundary.
- During work, report a completed work item, a changed plan, a failed check that changes the next step, or a real blocker.
- For long-running work, keep the host task and GitHub state current enough that a status request can name the active item, completed items, blockers, current proof, and next step.
- On completion, report the delivered outcome, verification, saved findings, merge state, and anything left `UNVERIFIED`.

Natural-language control maps to host controls where they exist:

| Owner request | Required behavior |
| --- | --- |
| "Show status" | Summarize current outcome, item, evidence, blockers, and next step |
| "Pause" | Stop new work and preserve recoverable state |
| "Continue" | Re-read Git, GitHub, and host task state before acting |
| "Do not merge" | Remove merge authority for all unfinished work |
| "Cancel" | Stop new actions, keep recoverable work, and report cleanup choices |

SkipHow must not claim that pause or resume survived a process restart unless the host confirms it. See the host capability note for the current difference between Codex and Claude.

## Findings outside the request

Delivery must not hide a material problem discovered along the way.

- Fix a blocking, unsafe, or inseparable problem in the current task.
- Save an independent, verified problem after a duplicate search.
- Record material uncertainty as `NEEDS_RESEARCH`.
- Dismiss a false or irrelevant signal with a reason.

In a read-only request, report the work item but do not write it to an external system unless the owner also granted persistence.

## Rejected alternatives

- Separate owner commands for bugs, ideas, CTO review, and unattended work. The categories overlap and force the owner to understand the implementation.
- A mandatory plan or specification before every change. Small, clear work should remain small.
- Automatic implementation after intake. Capturing a thought is not consent to change the product.
- Silent handling of unrelated findings. This loses useful work and makes unattended runs hard to trust.
- Constant progress narration. It consumes context and hides the few updates that matter.
- A custom status dashboard or task database. GitHub, Git, and the host already hold the durable state SkipHow needs.

## Limits and unverified items

- `UNVERIFIED`: implicit skill selection produces acceptable recall and precision on both packaged hosts.
- `UNVERIFIED`: the natural-language controls map consistently to every supported host version.
- `UNVERIFIED`: batch intake preserves provenance and avoids semantic duplicates on representative owner input.
- `UNVERIFIED`: unattended delivery can resume after compaction or restart without losing a product decision.
- `UNVERIFIED`: owners understand the difference between saving work and starting delivery from README examples alone.

Package checks can prove that manifests and references load. They cannot prove interpretation. These items need opt-in live tests with the exact packaged candidate.

## Revalidation triggers

Repeat this review when any of these events occurs:

- Codex or Claude changes skill discovery or explicit invocation syntax.
- A host changes Goal mode, pause, resume, session persistence, or worktree behavior.
- Live tests show frequent false activation or missed activation.
- Owners repeatedly ask which command to use.
- Intake creates duplicates or starts implementation without clear authority.
- A new tracker becomes a supported product target.

## Primary sources

- [OpenAI, Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI, Long-running work](https://learn.chatgpt.com/docs/long-running-work)
- [Anthropic, Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [Anthropic, Create plugins](https://code.claude.com/docs/en/plugins)
- [Anthropic, Keep Claude working toward a goal](https://code.claude.com/docs/en/goal)
