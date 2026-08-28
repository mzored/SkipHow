# Testing

For a read-only design or coverage request, report the proposed tests without changing the project. Write or change tests only when the requested outcome authorizes project changes. Test observable behavior through the narrowest stable interface that gives confidence in the requested result. Follow the repository's existing test layout and vocabulary.

Choose the cheapest test that can fail for the real defect or requirement. Prefer an integration-style path when isolated units would mock the behavior being proved. Mock external systems, time, randomness, or other true boundaries only when a real substitute is impractical. Avoid mocks of internal collaborators and assertions about call order or private state.

Use an expected value independent of the implementation. A test that repeats the production algorithm can agree with the same bug. Name the user or caller behavior that the test proves.

Write the failing test first when it provides a useful red signal and the needed interface already exists. For exploratory work, legacy behavior, or a change with no honest test seam, establish the behavior first and add the durable check at the right level. Test-first is a tool, not a ceremony.

Run the focused test and any broader suite the change can realistically affect. Confirm a regression test would have failed without the fix when that check is safe and practical. Keep tests that protect behavior; remove only temporary harnesses and implementation-coupled checks owned by this work.
