# Resolving merge conflicts

Use this for an active merge, rebase, cherry-pick, or revert conflict.

Resolve only when the requested outcome authorizes changing the conflicted work. Otherwise inspect and report without modifying the operation. Read the active Git operation, conflicting files, nearby history, and the intent of both sides. Use commit messages, issues, tests, and surrounding code as primary evidence. Do not treat conflict markers as enough context.

Resolve each hunk so the combined result preserves both intents when they are compatible. When they conflict, choose the behavior that matches the stated integration goal and current product contract. Do not invent unrelated behavior while reconciling code.

Preserve changes outside the operation. Do not abort, skip, or discard commits when that could lose unique or foreign work without the exact grant required by the root. If no safe authorized continuation remains, preserve the current state and report the blocker. Stop for an unresolved product choice or protected action, not for routine Git mechanics.

Run the relevant checks on the resolved state, inspect the resulting diff, and continue the requested Git operation to completion. Report any intent that could not be preserved and the evidence used for the choice.
