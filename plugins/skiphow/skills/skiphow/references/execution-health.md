# Execution health

Long or delegated work fails quietly more often than it fails loudly. Give every long-running step an expectation, and treat a breach as information rather than a reason to wait longer.

Before running a command, suite, build, service, or delegate that could take real time, decide what a healthy duration looks like and what would count as no progress. When the project offers no baseline, establish a conservative one and say so rather than waiting indefinitely. Record what actually happened: duration, result, attempts.

Treat a lane as anomalous when it breaches that expectation, repeats the same failure without new evidence, stays active without measurable progress, grows in scope or diff unexpectedly, or produces evidence that conflicts with another source. Divergence between local results, the shared branch, and any external system is itself an anomaly.

On an anomaly, stop that lane and keep independent work moving. Capture the smallest useful diagnostics, then classify the cause: implementation, test, environment, dependency, infrastructure, performance, coordination, specification, or external system. Correct the highest-leverage cause rather than the nearest symptom, rerun the smallest reproducer first, and resume only on new evidence.

Never silence a failure you cannot explain. Increasing a timeout, adding a retry, disabling or skipping a check, weakening an assertion, or accepting an intermittent pass are all changes that require a stated diagnosis first. Never reach for a bypass flag or a destructive reset to make a failing path go quiet.

When the same problem survives three genuine attempts, stop attempting. Three failures against one hypothesis usually mean the hypothesis is wrong or the design underneath it is mismatched. Step back and question the approach itself before a fourth attempt, and record what the three attempts ruled out.

Repeated workarounds are a signal about the system, not about the task. When the same failure pattern, manual step, or coordination defect recurs, fix the control that keeps producing it when that is within the requested result, and report it when it is not.
