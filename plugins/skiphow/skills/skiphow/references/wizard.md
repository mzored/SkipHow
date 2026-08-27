# Wizard

Use this method only within the authority granted by the owner request and the root contract. A how-to question or plan stays read-only. Build an artifact only when the owner requested a project change or tool, or when an already-authorized change genuinely needs it.

Inspect the repository and current official documentation before writing instructions. Identify every action only the human can perform, the value or confirmation it produces, where that result belongs, and which steps are reversible.

Build the smallest guided artifact the project can run easily. A script is useful when it can validate input, persist configuration safely, or resume after interruption. A concise interactive checklist is better when automation would add no value. Use the project's existing language and tools.

Present only the human actions the procedure needs. Sequence them when dependency or risk requires it; otherwise group safe independent actions. Explain what the person should see, and validate a result before relying on it. Open the exact current page when the environment supports it. Mask secret input, keep credentials out of logs and command history, and write them only to their intended secure destination.

Before an action the root classifies as protected, verify that its exact grant is already present. The wizard and completed setup steps do not grant that action, and the owner need not repeat a grant already given. An ordinary shared action already authorized by the requested outcome does not acquire another gate merely because a human-only step performs it.

Make repeatable operations safe to rerun. Check script syntax and statically trace every captured value to its destination without executing human-only or protected steps. Include the guided artifact in the ordinary project commit only when it is an owned, reusable tool covered by the current grant; otherwise keep it outside the project or remove it after the procedure succeeds.
