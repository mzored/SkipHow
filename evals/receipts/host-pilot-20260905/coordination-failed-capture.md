# Coordination experiment with failed capture

One explicit coordination diagnostic ran after the neutral pilot. The host
session completed, but the driver failed before retaining its stream or final
artifacts. Its exact final usage and cost are unknown. The configured session
ceiling was $1 including delegates, with a 900-second wall limit. There was no
automatic retry.

The failed driver's SHA-256 was
`ece0c3777c00f810171b2a29348282f47c638f1b2855e6801364cc415ce8ab63`.
The source used the same `catalog-integration-ready` fixture and package as
the neutral candidate. It requested one configured isolated writer with a
two-turn limit, one read-only reviewer, recovery of partial work, integrated
verification and delivery to the synthetic origin.

The signature sanitizer assumed every forwarded event's `message` was an
object. A string-valued message raised `AttributeError` after the host exited.
The surrounding temporary-directory context then deleted the only raw stream
and the fixture. This is a capture failure, not a model outcome or a complete
receipt. The destroyed stream has not been reconstructed.

`coordination-live-worktrees.json` is an independent operator snapshot that
survived. It records the main `fix/catalog` checkout and the host-created writer
checkout on a distinct branch, both based on commit
`203c8238a2478dfe210f89359c9a0cc338b2c110`. The writer's uncommitted pricing
repair is retained in its diff. Main-checkout repairs in progress are also
visible. This snapshot proves those narrow filesystem facts only. It does not
prove final integration, review, final foreign-file preservation, termination
reason, effort actually applied, or cost. Those capabilities remain unverified
for this attempt.

The repaired driver handles arbitrary JSON message shapes and retains a
sanitized stream plus final capture before optional parsing, destination
commands or grading. If complete capture fails, it preserves the ignored
private workspace and prints its recovery path. Deterministic injected-failure
tests verify those behaviors before any proposed repeat. The original neutral
pilot captures are unchanged.
