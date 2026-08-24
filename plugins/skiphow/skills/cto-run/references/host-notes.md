# Host notes

Host policy takes priority. The host provides the current session, capability mapping, command runner, durable storage, context measurement, task controls, and external-system connectors. The runbook names the project-specific locations and terminal condition.

Resolve the current session's available capabilities through host configuration. Record the selected capability and any limitation in the receipt. Do not encode provider names, personal directories, local executables, or launch commands in runbooks or policy files.

Use the host's normal task controls for bounded delegation, cancellation, and result collection. If a result will be consumed later, record its durable handle in the journal. If a host cannot expose a required capability or context measurement, record the gap, use the safest available process, and block only the dependent lane.

Before context loss, write a checkpoint with state, journal entries, receipts, and an updated briefing. After recovery, rebuild from durable artifacts and primary systems, then continue the same run. A context reset is a recovery boundary, never a terminal condition.
