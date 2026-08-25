# Codex ChatGPT OAuth evaluation

## Constraint

The project owner will not provision provider API keys or pay separately for model trials. Release evaluation may use only the installed Codex CLI, its existing ChatGPT OAuth login, and a deliberately small number of host invocations.

## Verified local behavior

- `codex login status` reports `Logged in using ChatGPT`.
- Codex CLI 0.149.1 documents that `--ignore-user-config` still takes authentication from `CODEX_HOME`.
- The managed marketplace policy permits the SkipHow Git source but rejects an arbitrary local marketplace path.
- After a normal marketplace refresh and plugin add, Codex reports `skiphow@skiphow` 0.9.0 enabled and its installed payload matches the candidate bytes.
- Codex `exec` has ephemeral execution and sandbox selection, but no documented hard token or dollar cap.

## Evaluation contract

The OAuth mode reuses the current `CODEX_HOME`; it does not copy or serialize OAuth material. The child process receives a minimal environment without provider API keys. Before every call, the evaluator requires ChatGPT OAuth status, one enabled SkipHow installation at the requested version, and a byte-exact installed payload. It starts Codex with `--ephemeral`, `--ignore-user-config`, and `workspace-write` sandboxing.

The operator must pass `--max-calls`. The evaluator derives the required invocation count from the selected scenarios and refuses a smaller value. This limits the number of model calls, not tokens inside one call. Receipts identify the authentication mode and retain `UNVERIFIED` profile isolation and cost claims.

## Remaining limits

This mode can provide outcome and restart evidence without API-key charges. It cannot prove isolated installation, provider billing, implicit skill loading, autonomous model selection, or a hard token ceiling. The mutable GitHub scenario still needs a separate repository-preservation boundary.

## First smoke result

One `small-fix` trial ran against commit `ede99adce4a4` with Codex CLI 0.149.1, ChatGPT OAuth, `gpt-5.6-luna`, low reasoning effort, and `--max-calls 1`. The checked workspace outcome and host process passed. The receipt kept the overall claim `UNVERIFIED` because Codex events did not prove implicit skill loading. Provider cost stayed unavailable. Host telemetry reported 55,825 total tokens for the single call.

That token count is too high for routine release checks under the owner's economy constraint. Do not run a broad live matrix by default. Prefer deterministic and package checks, and reserve another OAuth model call for a specific release question that cannot be answered locally.
