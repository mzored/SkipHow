# Paired evaluation: with and without SkipHow

A small paired comparison on 2026-08-26, one run per arm per task, same host and model, same fixture, same prompt. It exists to catch obvious regressions and overhead and to give later releases a baseline; three tasks with one run each cannot rank two systems.

## Setup

- Host: Claude Code 2.1.246, model `claude-fable-5`, `-p --permission-mode bypassPermissions --output-format stream-json`.
- With: `--plugin-dir plugins/skiphow` at the 1.4.0 candidate. Without: no plugin flag; the installed plugin was disabled. The owner's global `CLAUDE.md` applied to both arms.
- Fixture: an orphan copy of the lab shop at its original commit for every run (discount bug, hard-coded shipping rates that contradict `config/rates.json`, `tenacity` pinned and unused, three passing tests). No GitHub remote.
- Metrics from the transcript with `scripts/run_summary.py`: turns, cost as the host reports it, elapsed seconds, tool calls. Correctness and lifecycle behavior judged by reading the diff, running the suite, and checking what was written where.

## Results

| Task | Arm | Turns | Cost | Seconds | Outcome |
| --- | --- | --- | --- | --- | --- |
| Small bug ("10 percent discount gives a negative total, find the cause and fix it") | without | 4 | $0.29 | 18 | correct one-line fix, one test, 4 passed |
| | with | 6 | $0.42 | 23 | same fix, two tests, 5 passed, five-heading report; two later runs 7 turns $0.43 and 6 turns $0.40 |
| Brain dump ("triage these and save them", no tracker) | without | 4 | $0.51 | 48 | correct triage; "saved" as four files in the host's per-project auto-memory directory outside the repository, then asked two questions |
| | with | 7 | $0.57 | 47 | four blocks in `.skiphow/inbox.md` with type, disposition, priority and reason; nothing implemented |
| Retry feature ("make fetch_product retry with exponential backoff") | without | 7 | $0.51 | 49 | used the pinned `tenacity`; retries every `HTTPError` including 4xx and says so; created an untracked `.venv` |
| | with | 9 | $0.65 | 50 | used the pinned `tenacity`; retries only `URLError`, timeouts, and 429/5xx; 404 fails at once; stated where it searched; `.venv` created (gitignored); a second run retried 4xx too |

## Reading

- Overhead. The skill adds two to three turns (loading the skill and one or two references) and 20 to 30 percent of cost on tasks this small. Elapsed time is within noise.
- Correctness. Both arms fixed the bug and both reused `tenacity`. The host baseline is not weak; on a strong model the reuse rule mostly confirms what the model does anyway.
- Where the difference is. Without the skill, "save them" put the records somewhere the owner will never look for them (the host's memory directory for that checkout) and ended by asking the owner two questions. With the skill, the records are in the project with a disposition and a proposed order, and the report says what would need the owner's call. The retry policy differed in one of two runs (a 4xx allowlist), so that is not a stable signal.
- Lifecycle. With the skill every run ended with the five headings and named its limits; without it, reports were shorter and skipped what was not verified.
- Findings. The planted shipping-rate mismatch is only met by tasks that read `shipping.py`; see the [1.4 receipts](v1.4-receipts.md) for the findings runs.

## What this cannot show

Sample size is one per cell. Cost differences of a few tens of cents are within run-to-run variance (the three small-bug runs with the skill spanned $0.40 to $0.43; the two retry runs spanned $0.65 to $0.67). Token counts are folded into cost by the host. No task here needs delegation, so routing cost is not measured; the 1.1 and 1.2 receipts record delegated runs but have no baseline arm. Codex reports no dollar cost, so no Codex pairing was attempted.

## Repeat it

```sh
# fixture: an orphan copy of the lab shop (see docs/research/2026-08-26/v1.2-receipts.md for its shape)
claude -p "<task>" --permission-mode bypassPermissions --max-budget-usd 5 --output-format stream-json --verbose > without.jsonl
claude -p "<task>" --plugin-dir plugins/skiphow --permission-mode bypassPermissions --max-budget-usd 5 --output-format stream-json --verbose > with.jsonl
python scripts/run_summary.py without.jsonl with.jsonl
```

Run each arm in a fresh copy of the fixture, then compare the diff, the suite, and where anything was saved.
