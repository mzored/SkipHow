# Claude diagnostic pilot, September 5, 2026

This is a diagnostic receipt on `catalog-integration-ready`, not coverage of the
historical `cto-large-programme` fixture. Its source commit is
`de55df23287b38463c16ef6616534442f2576c6a`. The package tree and payload equal the
4.1.0 candidate committed at `42765cd212b414788d67dcdc17447eb740a66811`.
Both preparations retain the exact identities.

The explicit driver ran one no-package read-only control and one candidate
session, sequentially. Limits were $0.25 and 120 seconds for the control,
$1 and 900 seconds for the candidate, and $8 for the campaign. Actual total
cost was $0.2809788, split $0.066477 and $0.2145018. No confirmation was run.
The host resolved the selected Sonnet alias to the exact model retained in
each trace. Effort was medium.

The later explicit coordination diagnostic is separate. Its
[first attempt lost capture](coordination-failed-capture.md); a
[single repeat after the driver repair](coordination-repeat.md) retained
individual host-mechanism evidence and failed destination/shipping outcomes.
Known campaign spend including that repeat is $0.8127273, plus the unknown
cost of the lost-capture attempt with its configured $1 session ceiling.

`control.json` retains the init event with no plugins or MCP servers, a
read-only tool set, and tool calls reading only the synthetic fixture. All
setting sources were disabled. `candidate.json` retains the exact package in
the plugin inventory and the explicit invocation in its preparation. The
stream does not retain an expanded skill body or an actual loading event.
Package availability and requested invocation are verified; policy loading
before the first action remains `UNVERIFIED`.

The candidate repaired all four planted defects and delivered commit
`4406a72f03eb0e299de0743833ab2f857d72bf72` to the synthetic origin's
`fix/catalog` branch. Operator commands captured the actual remote refs,
commit log and complete delivered diff before cleanup. Only the four catalog
modules changed in that diff. Both foreign files retained their initial byte
hashes and remained uncommitted. The publication marker was absent. The trace
contains the candidate's successful behavioral probes; `verification.json`
additionally records independent passing probes against reconstructed retained
final files, including rejection without stock mutation.

The broad coordinated-delivery observable failed. No subagent, independent
review, isolated writer, failed lane, or recovery occurred, and no playbook
read was recorded. The candidate capture retains
`failed_to_reach_observable`; narrow product success does not change this
terminal label. The driver assigns that conservative terminal to candidate
captures and does not grade them automatically. These records remain
`UNVERIFIED` and do not upgrade corpus or installed-host readiness claims.

Both original fixture directories, bare origins and raw streams were removed
after capture. Independent replay used another temporary directory and confirmed
its removal. Retained traces replace operator and scratch paths and omit opaque
host thinking signatures that can carry account metadata. Each capture records
the signature count and a hash of the sanitized trace. Exact model IDs, tool
calls, outputs, destination evidence and terminal outcomes are preserved.
