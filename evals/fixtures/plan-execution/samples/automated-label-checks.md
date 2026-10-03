# Representative uniform-label checks

The existing exact-output checker computes the expected transformed catalogue from the original entries.
It detects any missing replacement, extra replacement, reordered parameter, or altered payload.
The compiler checks generated calls, and the compatibility reader checks accept the new label and old records.
Diff review checks the codemod and its bounded transformation. A file count alone adds no manual workload.
