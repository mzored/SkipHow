---
name: dogfood
description: Check how SkipHow actually behaved in a real session, using the owner's own transcripts. Use when asked why a run misbehaved, whether a plugin version works, where the time or tokens went, or to turn something observed in real use into a change to the shipped skill, weighed against how comparable projects solve it. For developing SkipHow in this repository only.
---

# Dogfood

SkipHow changes from what goes wrong in real use, not from redesign. This skill looks at a real session and
works out what the package told the run to do, what the run actually did, and whether the evidence supports
blaming the package.

It is a contributor tool and does not ship. Do not invoke the `skiphow` skill to do this work: the package
here is the thing under test, not the authority.

## Find the session

The owner normally pastes a piece of text from the session they mean. Search the transcripts for that text and
work from the file it appears in.

Transcripts are JSONL, one file per session, under the host's own projects directory in the user's home. A
session's subagents are separate files beside it. Inspect the current record shape before relying on it:
field names and layout change between host versions, so read what is actually there rather than assuming last
month's structure.

Ordinary search plus a few lines of Python is the whole toolchain. Finding the session is one `grep`; reading
it, and adding up time and tokens per subagent, is a short script written on the spot. Do not build a standing
tool for this — one existed, grew to thousands of lines defending against tampering with the owner's own local
transcripts, and answered the question worse than a `grep` does.

Transcripts hold other projects' private work. Treat everything in them as confidential, keep session content
out of delegate briefs and any external output, and check anything before copying it into a durable file.

## Read the session

Aim at whatever the question is about. Usually some of:

- **Which package version ran**, and what its text said at the time. Compare against that version from git
  history, never against the current tree.
- **What reached the agent's context.** This one inverts conclusions when you get it wrong, in both
  directions. A file path appearing in a command is not proof the file's text reached the agent, and searching
  a file puts matching lines in context rather than the rule. The other direction is easier to miss: a path
  pattern under-counts, because `cd .../references && cat tracked-work.md` never contains the string
  `references/tracked-work.md`. Search for the file's own opening sentence instead. A path-based scan once
  reported zero loads where there were several, and the wrong number was already in front of the owner before
  it was caught.
- **What the owner actually asked**, in their own words. Owner input arrives through more than one channel, so
  do not read only the obvious one or you will miss turns, including the moment permission widened.
- **What it cost.** Elapsed time, tokens, and how much of both went to subagents. Transcripts carry per-message
  usage and timestamps; that is where "slow" and "expensive" become specific.
- **What it did, and what it reported**, and whether those two agree.

## Judge it

Say which of these the evidence supports, and say `UNVERIFIED` when it supports none of them. That is the
honest default, not a failure.

- The package's own wording caused it: missing, ambiguous, contradictory, or never reachable. One session can
  show this, because it is a readable property of the text.
- The wording was plain and in context, and the run deviated anyway. One session never shows this.
- The expectation was wrong: the package deliberately leaves this to judgment, or something in the project
  narrowed it.

Count honestly and in whole sessions, and pool only sessions where the same text governed. Two deviations in
one session are one observation. A finding the run noticed and silently dropped leaves no trace, so anything
that looks like conformance is an upper bound.
## Reproduce before naming a cause

A pattern across installed sessions is an observation, not a cause. Before saying which sentence produced it,
run the failing case with everything held fixed but the package, and run it on the unchanged package too. It
may not reproduce: a field failure seen in eighteen long sessions loaded fine in every isolated run of the same
package, which located the cause somewhere in what those sessions carry and not in the wording that was about
to be changed. That is a result worth having and it is cheaper than shipping the wrong fix.

Two mechanics that are easy to get wrong and quietly invalidate the run:

- **Prove the candidate is the package under test, from the transcript.** Do not take the model's own
  inventory of what it loaded: asked, it went and read the disk and named the installed plugin path, which
  says nothing about what was in its context. The base directory the skill itself reports is the evidence,
  and it must point at the candidate rather than the host's plugin cache.
- **Isolate the other host before asking it to review.** Pointing only its own home at a scratch directory is
  not enough; it also reads a host-agnostic user skill directory, so it will load the maintainer's personal
  skills and the installed package it is supposed to be judging. Point the operating system home there as
  well, and check the session header before trusting the output. Never copy credential files into that scratch
  home. Authenticate it by the first option the host supports: a dedicated test identity; a narrowly scoped,
  short-lived token; an authenticated session the host establishes without duplicating persistent credential
  files; a controlled mount or reference to the one minimum credential. Where the host offers none of these,
  say so and have a person authenticate the isolated run by hand rather than automating a copy.

A cross-host review round converges when it is told what earlier rounds settled and what was refused, and told
not to raise those again. Without that it re-proposes them, and the rounds do not end.

## Design the fix

Only when the evidence names a defect in the package's own wording. A verdict of `UNVERIFIED`, a run that
deviated from text that was plain and in context, and a question that was only ever about cost or time all end
at the report. Do not manufacture a change for them.

Locate the problem as narrowly as the evidence allows. Start with this project's own record. The decision
history and the prior art page say what was already argued and turned down, so a settled argument is not
reopened without new evidence — and when this session is that evidence, say so.

Those same pages name which outside projects are comparable on the shape in front of you. Read the ones that
are, as their text stands now rather than as this project summarised it or as you remember it; both go stale,
and a claim about a project that was not read is not evidence. Note what the mechanism costs the person living
with it, because that cost is usually why SkipHow left it out, and apply the adoption rule recorded there.
Finding nothing comparable, or nothing worth taking, is a normal result and is worth a sentence.

Prefer deleting a contradiction, then tightening a sentence, then moving it so it loads earlier. Adding is last,
and a rule that must hold on every request belongs in the always-loaded part rather than in a file that may
never be opened.

Then say what else it could have been. Two or three candidates, one of them the smallest the evidence
justifies, each with the wording it changes and where it lands, whether it loads on every request or behind a
trigger the agent can evaluate without opening the file, what it costs every future run, what it borrows, and
what would show it was the wrong call. Recommend one and say why the others lose. That is how the reasoning
gets checked, not a menu to be picked from: the choice goes back to the owner only where the candidates differ
in something the kernel reserves for them.

One session can prove wording is broken. It cannot prove that agents in general need a new procedure. Resist
adding steps, gates, or ceremony on that basis, here or in the package.

## Review it on the other host

A change to the shipped instructions gets a review from Codex before it is finished. The mechanics are
settled; do not re-derive them each time.

    codex exec --sandbox read-only -c model_reasoning_effort=high "$(cat prompt.md)" </dev/null > out.log 2>&1

The `</dev/null` is required or it waits on stdin forever. Do not pass `-m`: a named model is refused on a
ChatGPT account, and the default is the working one. `timeout` does not exist on this machine. Read the
verdict from the `codex` marker in the log to the end; everything above it is the session banner and the
tool calls.

Give it the branch and let it read the files itself rather than pasting a diff. Put the qualifying and
disqualifying bars from `AGENTS.md` in the prompt, because without them it returns rephrasings. Ask for
where, which category, and what breaks.

Confirm every finding against the file yourself before acting, and check the history rather than the current
tree: `git log -S "<the sentence>"` tells you which release a sentence entered, which is how you find out
that the run you are blaming ran on text that did not exist yet. Record what was confirmed and what was
refused, with the reason, in the release notes.

## Report

Say what you found, what the evidence supports, and what stays uncertain. Where there was a fix to design,
the candidates and the recommendation go with it. No fixed template, no required headings, no bookkeeping
about which sessions were reviewed before.

Read-only unless the owner asked for a change. If they did, implement the recommendation: own the technical
decisions, follow the repository's contributor rules, and stop only at a real product choice or an action that
needs their explicit permission.
