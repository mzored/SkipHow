# Testing

Open this before writing, changing, or deleting a test, and when a suite is slow or flaky. The kernel's Engineering standard sets when a test pays for itself; this file is the method.

## Choosing the test

Choose the seams first. A seam is a public boundary callers use, such as an HTTP route, a command, a library function, or a page a user drives. A few tests there buy more than many tests at internal seams, which pin the implementation and break on every refactor. Use the repository's test layout, runner, and vocabulary.

Pick the cheapest level that can see the failure. A unit test at the interface covers a rule. A browser, database, or integration test earns its cost when the failure only shows there: rendering, persistence, a real protocol, or a journey across services. Repeat a business rule at a costlier level only when that level can fail in a way the cheaper one cannot see.

Mock only at system boundaries you do not control: the network, the clock, randomness, a payment provider, a third-party API. Assert on what the code under test returns or changes, never on the mock.

Compute expected values from the product rule, for example a fixed price and discount worked out by hand. Copying the implementation's output into the test repeats its bug.

When setup or an earlier journey is not what the test is about, reach the required state through a cheap reliable path, such as a fixture or a direct API call, instead of replaying the journey through the browser. Keep a direct test of a setup journey that matters to users.

Prototypes and spikes carry no tests. Add them when the code is kept, at the seam it ends up with.

## When the test comes first

Write the failing test first when the interface it needs exists and a red result tells you something. For exploratory work or legacy code with no honest seam, get the behavior working first, then add the test at the right seam, or none if the kernel's bar is not met.

## Bad test shapes

These cost more than they protect:

- Change detectors that pin text, copy, constants, configuration, CSS, or file layout.
- Tests of call order or private state.
- Tests of the project's own tooling, CI, scripts, or other tests.
- Source-reading tests that enforce code shape. Put a mechanical rule in the linter or type checker the existing check already runs.
- Tautologies: a test that passes whatever the code does.
- One test per reviewer worry, each guarding a case no plausible change would break.
- Several shallow tests of one behavior that a single interface test already covers.

## Cleaning up tests you touch

Replace, don't layer. When you write a better test at the interface, delete the shallower ones it covers in the same change. When a change breaks a test but not behavior, rewrite or delete that test rather than bending the code to keep it green.

In code you touch, delete change detectors and tests duplicated by an interface test. Removing them needs no more proof than adding them did. Keep the guards that protect money, security, customer data, and the release path: payment and balance rules, authorization and access checks, data isolation and deletion, and the build or install step a release depends on. A test of how a deploy script is written is not a release-path guard; a check that the built package installs is. If you cannot tell which kind a test is, read what it would catch before you delete it.

## Regression tests

The kernel decides whether a fixed bug gets a regression test. When it does, assert the rule the bug broke, not the literal inputs that exposed it, and place the test at the seam that owns that rule. Watch it fail against the unfixed code before trusting it. If no correct seam exists, report that as an architecture finding instead of writing the test at a wrong one. Where reproducing the bug is unsafe, rebuild the broken condition at the layer that owns the rule and say which part of the real path went unexercised.

## How much to run

Run the smallest set that shows the changed behavior works, and widen it for behavior the change can reach, boundaries it crosses, real uncertainty, and consequence. Run the project's required checks before integration or release; skipping one is not a cheaper substitute. Use the runner's own affected-test selection where it is reliable rather than path guesses.

Keep the check's own exit status and its failures when you shorten or filter output. A filter that succeeds proves nothing passed. Unknown status or output you cannot read stays `UNVERIFIED` until you establish it.

### Reusing a verification record

A pass is reusable when you can verify it: the command and arguments, the tree it ran on, its exit status, and where the output is, kept in an existing log, CI run, or handoff. No new file is needed. The relevant environment counts too: dependencies, configuration, ignored or external inputs, services, and destination. If the source changed while the check ran, or you cannot tell which tree it covered, the pass does not apply.

Delegates, leads, and reviewers reuse a verifiable pass for the same command, tree, and relevant environment. Accepting a return, reviewing, integrating, or reporting means inspecting that pass and the current inputs, not running it again. Rerun only for changed inputs, a missing or unverifiable result, or a concrete doubt you can name. Scratch files and service state can change without changing the tree, so check them when they matter. A different tree proves no current pass and needs its own, including revision-bound CI where the project has it. Changing role or stage invalidates nothing. Reuse never replaces a check the change still needs, an independent review it earned, or a check at the destination.

## Diagnose verification friction

When a suite is slow or verification keeps costing time, measure before choosing a remedy. Look at execution and setup time, dependency installation, service startup, test-data preparation, serialization, retries, duplicated coverage, and CI layout. Fix the layer that costs the time. Many browser tests do not prove the browser is the bottleneck, and a fast suite does not prove the important behavior is covered. Delete a test because it is a bad shape or a duplicate, never because it is slow or one of many.

Use the runner's parallelism and selection and the CI provider's caching before building a custom selector, queue, or gate. Custom verification tooling needs a measured need the native options cannot meet, and it is code the owner keeps.

Never make a suite green by skipping useful tests, weakening assertions, adding retries, raising timeouts, or moving a check out of the delivery path. A small fix to the verification setup that the requested change needs belongs in that change; a larger separable one takes the kernel's rule for a confirmed finding.

## Flaky tests

A flaky test is a defect, not noise. Classify it first, using [diagnosis](diagnosis.md): a race or ordering dependency in the product, shared state between tests, an uncontrolled clock or randomness, a real external dependency, or the environment. Then fix that cause. Never retry until green or mark it as allowed to fail. Until it is fixed, a pass from it proves nothing and it blocks a completion claim that depends on it.
