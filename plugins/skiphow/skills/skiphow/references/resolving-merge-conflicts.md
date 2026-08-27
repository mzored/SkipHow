# Resolving merge conflicts

Resolve only when the requested outcome authorizes changing the conflicted work. Otherwise inspect and report without modifying the operation. Read the active Git operation, conflicting files, nearby history, and the intent of both sides. Use commit messages, issues, tests, and surrounding code as primary evidence. Do not treat conflict markers as enough context.

Resolve each hunk so the combined result preserves both intents when they are compatible. When they conflict, choose the behavior that matches the stated integration goal and current product contract. Do not invent unrelated behavior while reconciling code.

Preserve changes outside the operation. Avoid aborting, skipping, or discarding commits unless the owner asked for that result or continuing would cause damage. Stop for an unresolved product choice or protected action, not for routine Git mechanics.

Run the relevant checks on the resolved state, inspect the resulting diff, and continue the requested Git operation to completion. Report any intent that could not be preserved and the evidence used for the choice.
