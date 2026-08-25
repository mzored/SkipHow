---
name: diagnose
description: Diagnose hard bugs and performance regressions whose cause remains unclear, reporting the cause for analysis requests or returning it to repair execution.
---

# diagnose

Use this temporary branch only when the cause of broken behavior or a performance regression remains unknown. Diagnosis proves a cause. It does not authorize a repair.

## Build a usable signal

Start with one repeatable check that reaches the reported behavior and can distinguish the failure from success. Prefer, in order, an existing or focused test, a CLI or HTTP invocation, a headless UI script, replay of a redacted trace, a small harness, a differential or bisection check, then a structured human-assisted reproduction as a last resort.

Run the check before forming a theory. It must exercise the reported symptom rather than a nearby error. Make it as deterministic and fast as practical. For intermittent behavior, measure repeated runs and raise the reproduction rate. For performance, record a baseline with a timing harness, profiler, or query plan.

If no usable signal is possible, record what was tried and the exact missing evidence. Exhaust repository evidence, available environments, tools, and bounded specialist work before asking the Owner for access, a redacted artifact, or a protected action.

## Reduce and test hypotheses

Minimize the reproduction one input, caller, configuration value, data item, or step at a time. Re-run the signal after each removal. Keep only elements required for the failure.

Create three to five ranked, falsifiable hypotheses when the evidence permits. For each one, state the observation or controlled change that would support or reject it. Keep this technical checkpoint internal unless Owner domain knowledge could materially change the ranking.

Test one prediction at a time. Prefer debugger or REPL inspection, then narrowly placed logs. Tag all temporary instrumentation with one unique marker so cleanup is searchable. Do not replace a missing signal with speculation or broad logging.

Stop when a probe distinguishes the verified cause from the alternatives and the original signal supports that result. Record:

- the reproduction command or procedure and observed symptom;
- the minimal case;
- the confirmed cause and the evidence that separates it from the rejected hypotheses;
- any limitation that leaves part of the claim `UNVERIFIED`.

Remove tagged instrumentation and throwaway harnesses unless the owning workflow deliberately keeps one as regression evidence. Redact credentials, authorization headers, personal data, and sensitive payloads from stored or shared evidence.

Return the cause and evidence to the controller. If the user requested diagnosis only, report without mutation. If repair is authorized, let normal execution select the repair and verification. Diagnosis alone does not require a campaign, tracker item, architecture change, or full review.
