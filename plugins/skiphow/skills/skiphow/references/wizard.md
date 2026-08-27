# Wizard

Use this method only within the authority granted by the owner request and the root contract. A how-to question or plan stays read-only. Build an artifact only when the owner requested a project change or tool, or when an already-authorized change genuinely needs it.

Inspect the repository and current official documentation before writing instructions. Identify every action only the human can perform, the value or confirmation it produces, where that result belongs, and which steps are reversible.

Build the smallest guided artifact the project can run easily. A script is useful when it can validate input, persist configuration safely, or resume after interruption. A concise interactive checklist is better when automation would add no value. Use the project's existing language and tools.

Show one focused step at a time, explain what the person should see, and report progress. Open the exact current page when the environment supports it. Mask secret input, keep credentials out of logs and command history, and write them only to their intended secure destination. Validate each result before advancing.

Place confirmation immediately before an irreversible, production, paid, or externally visible action. The wizard guides that action but does not grant it.

Make repeatable operations safe to rerun. Check script syntax and statically trace every captured value to its destination without executing human-only or protected steps. Commit only an owned, reusable project tool covered by the current grant; otherwise do not create a project file or remove a temporary artifact after the procedure succeeds.
