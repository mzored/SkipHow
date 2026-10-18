---
name: skiphow-simplify
description: Shrink an existing project by measuring it, removing code, tests, tooling, and records that do not pay for themselves, and delivering the cuts through the project's normal path. Use only when the owner asks to simplify, clean up, slim down, or shrink the project or codebase; not for ordinary changes, bug fixes, or a refactor inside other work, and not for a bare clean that ends an iteration session, which is a delivery request. If context was compacted while this workflow governed, reopen this file and the SkipHow CTO skill before the next consequential action.
---

# SkipHow simplify

Make the owner's project smaller and cheaper to change without losing behavior a user or caller would notice. Before consequential work, and again after any context compaction, load the [SkipHow CTO kernel](../skiphow/SKILL.md) by invoking the `skiphow` skill where the host has a skill tool, otherwise by reading it, unless its full text is already in context; a summary is not its text. Its Engineering standard is the measure for every cut.

## What the request grants

An owner's request to simplify, clean up, or shrink the project is a change and delivery request: carry the cuts through the project's established non-production workflow without asking again. A question about what could be cut stays read-only and returns what you would remove and what it would save. Material deletion of data, history others share, production changes, and other protected actions still need the kernel's grant. Deleting code, tests, tooling, and documents through reviewed commits is ordinary engineering.

## Measure first

Get the numbers before you cut, from what the project already has: lines of product code, test code, and the project's own tooling counted apart; suite and CI wall time; and git hot spots, meaning the files changed most often and how many of those changes fixed the project's own tooling or tests. Keep the numbers in working state, not in a new file.

## Find what does not pay

Look for these first, because they are where agent-built projects grow:

- Tests of the project's own tooling, CI, scripts, or other tests.
- Change detectors and duplicate tests, and other shapes [testing](../skiphow/references/testing.md#bad-test-shapes) lists.
- Tests that read source files to enforce code shape.
- Custom selectors, gates, queues, wrappers, or report generators that duplicate the test runner, the CI provider, or the linter.
- Shims and compatibility paths whose only callers are in the repository.
- One business rule copied in several places.
- Production branches, helpers, flags, or doubles that exist only for tests.
- Plan, report, and analysis archives.
- Dead flags and options set the same way everywhere they are read.
- Project instructions written by earlier sessions that make agents add artifacts.

For each candidate, ask what a user or caller would notice if it were gone. If nothing, it goes. Before removing a compatibility path, check for outside consumers that exist now. When a flag's live value is only visible in production, read it only within the kernel's limits for production reads, or leave the flag and say why.

The agents and CI jobs that run the project's own tooling, gates, and limits are not the callers that justify them. Judge each, hot spots first, by what it costs per run and in fixes against what it catches and what the test runner, CI provider, linter, or a maintained library offers, checked in their current documentation; then replace, shrink, or keep it on that evidence.

## Keep the guards that protect

Guards for money, security, customer data, and the release path stay, as [testing](../skiphow/references/testing.md#cleaning-up-tests-you-touch) describes. When such a guard has a bad shape, replace it with a good one in the same change rather than dropping the protection. For example, a test that greps a handler for a role check becomes a request without that role that the interface refuses. A cut that relies on another test covering the same behavior holds only after you open that test and see it assert that behavior.

## Carry it through

Decide what goes yourself; do not hand the owner a menu of technical cuts. Ask only about a cut that would change visible behavior, a support promise, or compatibility for a real outside consumer, because those are product decisions.

Deliver the cuts in reviewable units, each one kind of removal with its tests, docs, flags, and CI jobs going with it, through [integration](../skiphow/references/integration.md). Each unit keeps behavior unchanged and the project's required checks passing. When a removal breaks a test but not behavior, the test goes too. Review each unit at the depth [review](../skiphow/references/review.md) sets for its consequence; most deletions need no independent reviewer. Use [technical design](../skiphow/references/technical-design.md#reuse-before-custom-code) when replacing custom tooling with the runner's or CI provider's own features.

## The rules that made the waste

Revise project instructions, limits, and tooling that earlier sessions chose when they generated what you removed or force needless work, such as a rule that every fix gets a test or that each run writes a report. A rule is the owner's only where their own words set it, in their messages, issues, or history; commits under the owner's account and their pick from options an agent offered do not make it theirs. Keep what the owner's words ask for, such as small modules, and revise the mechanism an agent chose for it, such as a line limit with a baseline to maintain. Rules the owner set stay; propose the change to the owner with what the rule has cost.

## Measure again and report

Take the same measurements on the delivered state. Report the before and after numbers, what was removed by kind and what it saved, guards kept or replaced, rules revised and changes proposed, and anything left with the reason.
