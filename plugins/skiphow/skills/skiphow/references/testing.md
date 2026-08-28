# Testing

For a read-only design or coverage request, report the proposed tests without changing the project. Write or change tests only when the requested outcome authorizes project changes. Test observable behavior through the narrowest stable interface that gives confidence in the requested result. Follow the repository's existing test layout and vocabulary.

Choose the cheapest test that can fail for the real defect or requirement. Prefer an integration-style path when isolated units would mock the behavior being proved. Mock external systems, time, randomness, or other true boundaries only when a real substitute is impractical. Avoid mocks of internal collaborators and assertions about call order or private state.

Use an expected value independent of the implementation. A test that repeats the production algorithm can agree with the same bug. Name the user or caller behavior that the test proves.

Write the failing test first when it provides a useful red signal and the needed interface already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level. Test-first is a tool, not a ceremony.

Run the focused test and any broader suite the change can realistically affect. Confirm a regression test would have failed without the fix when that check is safe and practical. Keep tests that protect behavior; remove only temporary harnesses and implementation-coupled checks owned by this work.

A regression test should close the class of bug, not the one reproduction. Observe it failing against the unfixed code before trusting it, and confirm the failure message names the invariant that was violated rather than reporting that something was not true. Assert the rule the defect broke rather than the literal inputs that exposed it, and place the test at the lowest layer that owns that rule. When a bad value crossed several boundaries, cover each boundary it crossed.

Scale verification to what the change can reach rather than rerunning everything after every edit. Start with the smallest targeted check that covers the change, widen to the affected module or contract, then to cross-boundary behavior where the change crosses one, and finally to whatever the repository requires before the work is integrated. Rerun anything a rebase, merge, dependency change, or generated artifact has invalidated.

A retry is diagnostic information, not permission to call an unexplained failure a pass. An intermittent test is a defect or an explicit blocker until it is classified, and a passing suite is necessary rather than sufficient: the behavior itself still has to be right.
