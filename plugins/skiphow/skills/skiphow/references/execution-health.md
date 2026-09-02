# Execution health

Use this before starting a step that could take real time, and for a stalled lane, a repeated failure, or a work stream accumulating repairs, integration conflicts, sibling invalidation, or delivery and process work without new evidence of the requested result.

Long or delegated work fails quietly more often than it fails loudly. Give every long-running step an expectation, and treat a breach as information rather than a reason to wait longer.

## Setting the expectation

Before running a command, suite, build, service, or delegate that could take real time, decide what a healthy duration looks like and what would count as no progress. When the project offers no baseline, establish a conservative one and say so rather than waiting indefinitely. Record what actually happened: duration, result, attempts.

## Observing a live lane

Once a lane has a live handle, remains inside that expectation, and belongs to no work stream whose shared premise is under review, leave it running. Observe it when the result can change what you do next: it completes, asks for attention, breaches the expectation, or another result makes its output newly relevant.

Prefer the host's event or wait mechanism to repeated status reads, and never hold the root's own turn open to poll. A sleep loop or a blocking command that occupies the root while lanes run is not a wait but a stop, and it costs the run every minute it holds. If the host permits only bounded waits, choose the longest bound the host and expected breach allow. An expired wait with unchanged state is not new evidence. Renew the wait without another inspection, narration, or decision pass.

## When a lane is anomalous

Treat a lane as anomalous when it does any of these:

- breaches the expectation set for it
- repeats the same failure without new evidence
- stays active without measurable progress
- grows in scope or diff unexpectedly
- produces evidence that conflicts with another source

Divergence between local results, the shared branch, and any external system is itself an anomaly.

On a lane anomaly, stop that lane and keep independent work moving. Capture the smallest useful diagnostics, then classify the cause: implementation, test, environment, dependency, infrastructure, performance, coordination, specification, or external system. Correct the highest-leverage cause rather than the nearest symptom, rerun the smallest reproducer first, and resume only on new evidence.

## When a work stream is anomalous

Treat a work stream as anomalous when repairs or integration conflicts keep growing, when sibling changes repeatedly invalidate one another, when delivery machinery delays the product work it exists to protect, or when technical and process work keeps expanding without new evidence of the requested result. A unit that must create a new prerequisite of its own before it can finish is the same signal.

Stop affected lanes at their next safe boundary, admit no new work to that stream, and apply [campaign direction](campaign-direction.md). Keep independent work moving. Resume only after the cause is addressed and at the capacity current evidence supports.

## What you may not do to a failure

Never silence a failure you cannot explain. Increasing a timeout, adding a retry, disabling or skipping a check, weakening an assertion, and accepting an intermittent pass are all changes that require a stated diagnosis first. Never reach for a bypass flag or a destructive reset to make a failing path go quiet.

When the same problem survives three genuine attempts, stop attempting. Three failures against one hypothesis usually mean the hypothesis is wrong or the design underneath it is mismatched. Step back and question the approach itself before a fourth attempt, and record what the three attempts ruled out.

Repeated workarounds are a signal about the system, not about the task. When the same failure pattern, manual step, or coordination defect recurs, fix the control that keeps producing it when that is within the requested result, and report it when it is not.
