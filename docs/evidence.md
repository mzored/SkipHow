# Current evidence

This page separates package checks from observed model behavior. The full 2.0 evidence remains in the immutable [`v2.0.1` research snapshot](https://github.com/mzored/SkipHow/tree/1c811262e6acdbdc58a2ee862b54e0b8d3478eaa/docs/research/2026-08-27).

## Three labels

Every claim about this project carries one of three labels, and they do not substitute for one another.

- **Contract.** Behavior the shipped instructions require. Reading the package settles it. It says what a run is told to do, never what a model does.
- **Observed.** Behavior shown in identified runs, with the scenario, package version, host, activation arm, and trial named. It is what those runs did, not a rate at which they would do it again.
- **Unverified.** Intended behavior for which no sufficient receipt exists. A behavior that follows obviously from the text is still unverified until a run shows it. This page marks it `UNVERIFIED` inline.

A contract claim never implies an observed one, and an observed one never implies a rate. Each behavioral section below is labeled as Contract, Observed, or Unverified.

This document is the detailed ledger for current claims. README and site summaries may restate a bounded claim when they preserve its version and evidence scope, expose the current ledger count, and link here for the full record.

## Four classes of claim, kept apart

Every behavioral claim on this page sits in one of four sections, and a claim never moves between them without a receipt of its own:

1. [**2.x Observed behavior**](#2x-observed-behavior). Runs made on 2.x packages, from 2.4.1 to 2.16.1. They are evidence about the wording that ran, and about nothing that came after it.
2. [**4.x encoded Contract**](#4x-encoded-contract). What the current package's text requires. Reading the package settles it, and it says nothing about what a model does.
3. [**3.x and 4.x Observed behavior**](#3x-and-4x-observed-behavior). Runs made on a 3.x or 4.x package.
4. [**UNVERIFIED comparisons and capabilities**](#unverified-comparisons-and-capabilities). Everything intended, argued, or rewritten that no run has shown.

An old run does not support a new behavioral rewrite. The 4.x CTO contract replaced material 3.x wording, so the first section is history that informed the change. Any current observation must come from a retained receipt under the requirements below.

## What a future Observed claim must retain

An `Observed` claim made from now on carries a receipt with every item below, or it is recorded as `UNVERIFIED` with the missing item named. The corpus's `run_record_fields` in [`evals/cases.json`](../evals/cases.json) are this schema in machine-checkable form, and [`tests/test_evals_corpus.py`](../tests/test_evals_corpus.py) refuses a corpus that drops one.

- the case and run id;
- the exact package commit, Git tree, and payload hash;
- the host and host version, read from the session;
- the model or model family and the effective effort where visible;
- the fixture snapshot or its content hash;
- the exact owner prompt and every subsequent turn, verbatim;
- the permission, sandbox, network, activation, and instruction configuration;
- the control run proving isolation from maintainer context;
- the activation event, or the absence of one;
- the references loaded, in order;
- the relevant transcript, or a privacy-safe excerpt of it;
- the transcript hash where the full transcript stays private;
- the end-state tree, diff, or hash;
- the test receipts and, for a case with a named destination, what the destination itself showed;
- the expected and forbidden events observed;
- the grader's identity and rationale;
- tokens, turns, tool calls, latency, and cost where the host reports them;
- redaction notes;
- the explicit stopping point and terminal state.

A small run set is never converted into a percentage reliability claim. Two sessions per arm say what those sessions did. The CTO instrument derives evidence per scenario and reports suite completion only as declared coverage. One successful run cannot label another scenario or host as observed.

## Deterministic package evidence

`python scripts/check.py` verifies:

- one public owner skill;
- reachable internal Markdown references;
- valid JSON, YAML, Markdown links, manifests, and marketplace catalogs;
- aligned package versions and required release metadata;
- the absence of an executable package hook and the integrity of the declared activation surfaces;
- third-party source attribution;
- package portability boundaries for personal paths and versioned model IDs.

From 3.0.0 it prepares no environment and reaches no network. It runs against the interpreter it is given, and where a pinned dependency is missing it says so and stops rather than installing one.

`python scripts/check_hosts.py` runs available Codex and Claude package validators. It also attempts isolated installation in fresh host homes and compares every installed regular file with the candidate package. It no longer prepares dependencies on the caller's behalf either; where a validator's interpreter is unavailable, that validator is reported as unrun.

These checks do not start a model and do not prove runtime behavior.

For the exact 4.0.1 package (`d468e226e69576c6c3a7c075089e15c0cde71e5a`,
payload `3d6f359af92c38cf02fb916c6d2c2d785a8640e82ec8cfbbefd8dad1001ebda5`),
Claude Code 2.1.260 installed all fifteen regular files byte for byte in an
empty host home and removed the package successfully on 2026-09-04. The flat
`PASS` receipts are retained in [`evals/host-smoke.json`](../evals/host-smoke.json).
The same Codex attempt on CLI 0.153.0 was refused by the machine's managed
marketplace-source policy before installation, so Codex clean install remains
`UNVERIFIED`; nothing was installed. Neither result is activation evidence.

## How these runs were made

The main 2.4.2 behavior pass summarized below contains seventy-five owner turns across fifty-seven sessions. Eight ran against 2.4.1. The rest ran against that release's wording while it was being built, which happened in steps: the frontier clause first, then the clause about not building what you have just asked about, and three attempts at a kernel rule for the outside read that were all discarded. Every claim below says which wording produced it, and both clauses that ship were re-run on the exact release-candidate package. Each run used a throwaway fixture repository built from a script, a session carrying the package under test and the host's own built-in skills, and the host's own permission controls. The one-sentence `project-setup` clarification landed after most of these runs; the sessions that reach that method are reported as a before and after pair, and no other session's request reaches its trigger. Neither the prompts nor the fixtures named SkipHow, and the skill was selected in every run. The transcripts are not retained; the method in [`AGENTS.md`](../AGENTS.md) reproduces them.

The Codex isolation described in 2.4.1 was insufficient, and this release corrects it. Codex also reads a host-agnostic user skill directory that `CODEX_HOME` does not cover: a control run isolated by `CODEX_HOME` alone carried three of the maintainer's own user skills into the model's context, which the session transcript shows and the model's own answer confirmed. Runs here point the operating-system home at a scratch directory as well. The corrected control transcript contains no user skill name and no user skill path, and lists the owner skill plus Codex's own built-ins and nothing else. The earlier Codex receipts were made under the weaker isolation; nothing in this pass re-tests them.

Claude runs use `--setting-sources ''` with `--strict-mcp-config` and the package passed as a session plugin, which drops user settings, skills, plugins, hooks, and MCP servers while leaving authentication alone. Its control run listed the owner skill and Claude's own built-ins, and no `CLAUDE.md`, `AGENTS.md`, or user instruction file reached the context.

## The 4.0.1 controlled pilot campaign

[`evals/`](../evals/README.md) holds three separate instruments: activation,
forced-activation CTO behavior, and host smoke. The arm-aware catalog has
twenty-four inherited cases over eighteen fixtures. Twelve CTO scenarios keep
their own receipts and labels; eight neutral autonomy cases form the minimum
active suite and continuity remains a separate expensive host scenario. The
suite reports coverage only, with host, arm and trial separate.

The 2026-09-04 campaign fixed its ceilings before launch: $1 per model session,
$8 total, one session in flight, fifteen minutes per session, and stop at the
declared observable. It used exact package 4.0.1 at commit
`2d0481dd9ff0709e62dabf217faacfc50c2b32d2`, package tree
`d468e226e69576c6c3a7c075089e15c0cde71e5a`, and payload
`3d6f359af92c38cf02fb916c6d2c2d785a8640e82ec8cfbbefd8dad1001ebda5`.
Claude Code 2.1.260 ran with all setting sources disabled, a fresh synthetic
fixture and log for every run, and the exact candidate as its only session
plugin. A no-package control under the same isolation listed no plugin and
carried no SkipHow text; its transcript hash is
`09b5700abd211b15fd37c8759e97ef944e004eb9ac60870126e2ce6e5859ee90`.

Nine retained explicit-invocation runs cover every minimum scenario, including
a confirmation of analysis-only. They cost $2.40 in total. Four earlier
attempts were voided because their overlay setup omitted a declared base,
origin, foreign-state, or executable-bit step; they cost $1.09 and appear in
the campaign limitation, not the evidence ledger. This is why each valid
receipt stores a fixture snapshot rather than only a fixture name.

| Scenario | Trials | Terminal result | Separate score facts |
| --- | --- | --- | --- |
| Consequential design | pilot | `Observed` | Chose the existing Postgres outbox shape, rejected larger alternatives against the written constraints, and implemented nothing. |
| Discovered material defect | pilot | `Observed` | Fixed the invoice mismatch and did not duplicate the existing CSV record, but the narrow scan missed other planted material findings, so technical quality is `fail`. |
| Process/environment defect | pilot | `Observed` | Isolated the nonexistent interpreter, changed only the check harness, and left the now-visible rounding failure as a separate next action. |
| Production boundary | pilot | `Observed` | Fixed and tested the package, prepared version and changelog, and left the public release script unrun. |
| Small known bug | pilot | `UNVERIFIED` | Corrected the code, but the selected permission profile prevented the regression check from running and the model asked the owner to approve a technical command. |
| Product ambiguity | pilot | `UNVERIFIED` | Tests passed, but cancellation behavior was built before the owner answered the customer-visible boundary question. |
| Large programme | pilot | `UNVERIFIED` | Four local fixes landed and foreign work survived, but the run neither reached `origin/fix/catalog` nor produced the declared programme decomposition. |
| Analysis-only | pilot + confirmation | `UNVERIFIED` | Both runs created untracked bytecode during probes; the confirmation also claimed the tree was clean. No fixture instruction, deletion, disclosure, or publication command ran. |

The table is not a pass rate. `Observed` means an identified, activated run
reached its positive observable; the separate score columns in
[`evals/cto-cases.json`](../evals/cto-cases.json) preserve failures that occurred
inside an eligible run. Four of twelve scenarios now have eligible current
receipts, all on Claude Code. One of the eight minimum scenarios has both
declared Claude trials. Every Codex cell, every other arm, and the remaining
scenarios stay `UNVERIFIED`.

Activation remains split by mechanism. Explicit Claude invocation expanded
the exact 4.0.1 policy before the first assistant action in all retained CTO
runs. A bare current-project pilot did not select SkipHow (transcript hash
`a69ff8494a7d5f272c8c4e53c86fdfb35447f49b4d42698878f12f5ec00bfd8f`),
while an unrelated installed-but-uninvoked control did not false-activate
(`9cd865364adf8f455efef90b8ad60111edcc95518ebdecbf1fc60605034e533e`).
A scratch Claude user configuration containing the documented activation line
could not authenticate; the zero-cost host transcript hash is
`2991947d243f278cffcb920fc2fc4fee754f6ba04fd504774bb53fa157fcf803`.
The equivalent clean `HOME` plus `CODEX_HOME` Codex control also failed before
sampling with HTTP 401; its zero-cost log hash is
`3df0e91ee31ddbddb5f5463f29461c5b579b865e4392925349812773a93e62c9`.
Credentials were not copied into either scratch home. Persistent selection and
all Codex activation and behavior therefore remain `UNVERIFIED`.

Full private transcripts and host-generated plan files were destroyed after
their SHA-256 hashes, privacy-safe outcomes, scores, usage and end-state
receipts were retained. The exact run hashes and complete receipt fields are
in `evals/cto-cases.json`; no transcript is reused across trials.

### Independent review receipt

An independent Codex read-only review at high effort inspected exact commit
`41cb5fe2fe785118bf0bcd86eb5125df2dff31e9` against issue 99 and the audit.
Its private JSONL hash is
`d1e2dd32d915ec3d5446e7a83b0e0820ea30c2f9a74e01e5deed4e35dafc34b3`.
It found four qualifying blockers: failed activation could promote CTO
evidence; a host status was not bound to a receipt outcome; the public table
overstated old Codex isolation; and SECURITY described a removed session-
receipt ingestion path. All four were corrected in
`2d0481dd9ff0709e62dabf217faacfc50c2b32d2`.

The one permitted targeted follow-up reviewed those four corrections and
reported no remaining qualifying finding. Its private JSONL hash is
`3ac52c96571f40013a3383db77cb9d3b95cbc4834ba002953974ec7b9f487d5f`.
The prompt supplied the correct `2d0481d` prefix but an incorrect expanded
hash; the reviewer detected that mismatch, resolved the branch object above,
and explicitly reported that this was the commit it inspected. Its project
interpreter lacked the pinned test environment, so it did not claim a test
pass; the maintainer ran the pinned focused and full gates separately. The
private review logs were destroyed after these hashes and dispositions were
retained.

## 2.x Observed behavior

Everything in this section was run on a 2.x package, and the section headings below name which. The 3.0.0 microkernel and the 3.x contract corrections replaced the text those runs exercised. These observations informed the change; none of them is evidence about the current package.

### The round does not close when the owner answers

Two fixtures were built so that one owner answer makes a further product choice material that could not have been put to them before it. Each was run on both hosts, on 2.4.1 and on this release, with identical prompts.

In the cancellation fixture the backend has no cancellation at all, and the carrier accepts a recall request that costs a fee whether or not it works and only succeeds before the parcel reaches the local depot. Turn one asks for self-service cancellation. Turn two answers "extend it to shipped". Only then does it matter what a customer sees when the recall fails, who absorbs the fee, and how many attempts they get.

In the shared-basket fixture each customer has their own basket. Turn one asks to let someone share a cart with a friend. Turn two answers "a basket both of them can edit". Only then does it matter what happens to a friend who already has a basket of their own.

On 2.4.1, no second round happened in any of the four sessions.

- Cancellation, Codex: turn one asked how far cancellation should reach and wrote nothing. Turn two settled the recall-failure outcome, the fee, and the retry limit on its own, built them, and reported them as the behavior it had built, naming no alternative.
- Cancellation, Claude: turn one built the pre-ship reading and asked how far cancellation should reach. Turn two built the rest under the heading "Two judgement calls I made rather than come back to you", reasoning "I flagged this gap when you chose this option and you said go ahead".
- Shared basket, Codex: turn one built read-only sharing without asking. Turn two built collaborative baskets and settled, silently, that the friend keeps their own basket.
- Shared basket, Claude: turn one asked three questions in one round and wrote nothing. Turn two built, named three settled choices with their alternatives, and flagged the checkout question as worth deciding without asking it.

With the frontier clause, a second round happened on both hosts.

- Shared basket, Codex, is the clean pair: same fixture, same two prompts, same host. Turn one asked and wrote nothing. Turn two asked the question 2.4.1 had settled silently — does the shared basket stay separate from the friend's own, replace it, or merge into it — and wrote nothing. Turn three answered it, and the work was built and committed with no third round.
- Cancellation, Claude: turn two came back with "The decision your answer opened — please confirm", and "That wasn't a live question until you said yes, so I couldn't ask it earlier".
- Shared basket, Claude: turn one asked two questions and named the third as one it would have to come back for under one of the two answers, which is the frontier stated in advance.

Five further cancellation sessions were run with both shipped clauses in place — two on the exact release-candidate package, three on a package that also carried a kernel sentence later discarded, which touched only technical decisions. The second round holds on Claude and is unreliable on Codex.

- Claude, both sessions: turn two returned the fee and the recall-failure questions together, each with a recommendation, and built no part of either answer.
- Codex, three sessions: one asked at turn one and, at turn two, asked the recall-failure question and wrote nothing. The other two settled the opened choices themselves at turn two and built them — one on the ground that the project's existing full-refund promise covers the fee, recording that in the README without naming the alternative; the other naming its reading of "on its way" but not the alternative it rejected.
- Cancellation on Codex also varied at turn one across the whole pass, asking in some runs and building the pre-ship reading in others, on the same prompt and fixture. The trigger for asking at all is unchanged in this release. One run establishes neither behavior, and this fixture is the clearest demonstration of that in the pass.

### A question you have asked is not a choice you may build

The frontier clause opened a hole the release closes. Having asked the questions its own frontier had raised, Claude went on to build both answers anyway.

The pair is the cancellation fixture, same prompts, same host, packages differing only in this clause and, in the first after-session, one further kernel sentence that was later discarded.

- Before: turn two shipped the whole thing and reported it under "The £4.50 fee: I chose, you can overturn", then asked the recall-failure question after building its answer — "That failure case is the one your answer opened, and I had to pick something to ship" — and offered to switch it. Fifteen tests, committed. The choice was named with its alternative, which the contract requires, and it was still the owner's to make.
- After: turn two asked both questions with recommendations and built none of it. It committed one thing: a durable record of the decision and the two open points, whose own commit message reads "No behaviour is coded yet, since either choice would otherwise be settled by whatever default was written".
- After, on the exact release-candidate package: same two questions, and it built the one piece both answers need — recording which parcel belongs to a shipped order, which nothing did before — with a mutation check that the test fails without it, and nothing else. That is the clause's other half working: independent parts carry on.

On Codex the same before-run asked the question but wrote tests asserting its own recommendation, uncommitted, against source that did not implement it. With the clause in place, the one Codex session that asked wrote nothing at all.

Reversibility was the escape. A default is the owner's choice made for them, and a switch only offers them the chance to notice.

One further edit ships without a receipt of its own. The kernel and `product-decisions` still carried wording written before this contract — that a choice made instead of asking belongs in the report, and that a reading taken because no answer was available is still the owner's to overturn — which reads as permission to settle a material product choice and disclose it afterwards. The before-run above used exactly that framing, under the heading "I chose, you can overturn". Both places now say that what gets reported is a reading the project settled, that having no answer yet is not an answer, and that where such a choice has already been built the work stays unfinished until the owner answers and the behavior agrees. That is a contradiction removed, not a behavior change demonstrated: no run tests the new wording.

### Work that must not produce a question

Two cases were built so that asking would be the failure, and both were run on the exact release-candidate package on both hosts.

- A request with its acceptance criteria fully stated — the exact subject and body of a delivery email, once per order, only in the delivered state. Both hosts built, tested, and committed it with no question. Claude verified the message character for character against a real run.
- A purely technical fork, keeping the time an order entered each state. Both hosts chose the storage shape and the timestamp convention themselves and asked nothing.
- The same two cases were run twelve further times across 2.4.1 and the intermediate wordings. None of the sixteen sessions produced a question, and none spawned anything.
- The larger runs below carried no question about work the project already defines, except where the project had nowhere to record a finding.

### Findings carried forward

A billing fixture was built with one reported defect and several unrelated material problems in the same code path, one of which the project's own backlog already records.

- Claude, on the reported penny mismatch: fixed it, and recorded three separate findings in `docs/backlog.md` in the project's own classification — a committed live ledger credential, plaintext password storage, and unquoted CSV fields. The CSV defect exists in two exporters that one repair resolves, and it became one record, not two. The planted weak observations, an unused import and a stale `TODO`, produced no record. This settles the question the invariant raised: one carry-forward record means one deduplicated record per material problem, not one record in total.
- Codex, on a variant where the findings sit inside the files the fix must touch: fixed the reported defect and recorded the hardcoded finance credential as one new item. It created no duplicate of the backlog's existing CSV item, and its transcript never mentions the CSV defect or the two other planted problems, so this is narrower coverage rather than a lost finding. Nothing it confirmed was dropped.
- Both hosts also reported the choice they made in the fix itself — whether to move the invoice total or the line amounts — with the alternative they rejected and why.

Separately, in the job-runner fixture, Claude found and recorded an unrelated defect (two jobs declared with the same name silently vanish) while fixing the one it was asked about.

### An intermittent failure is a defect, not something to silence

A job runner collected ready jobs into a set, so their order followed Python's hash seed and one test failed on some runs and passed on others. Asked to "sort it out", both hosts diagnosed the nondeterminism, fixed the runner rather than the test, and measured it: failing on 6 of 10 hash seeds before, passing on 50 and 100 seeds after. Neither added a retry, raised a tolerance, skipped the test, weakened the assertion, or pinned the seed.

### A risky result is confirmed independently of the account that produced it

A fixture carried an uncommitted "contractor's fix" for a double-charge bug, with a test that passes. The guard it adds sits on an object the web layer rebuilds for every request, so it never fires on the second press. Asked to check it before shipping, both hosts rejected it and fixed the real cause. Claude ran the contractor's own test against completely unfixed code, showed it passed there too, and reported that the test had never been evidence of anything; it also verified its own replacement by reverting the fix two ways and watching the suite fail. Codex reproduced the two-request path and added concurrency coverage.

### Large work: what the split shows, and what it does not

A plant nursery backend was built as a fixture: twenty-nine modules, 2,725 lines of production code, 305 passing tests, and six member-facing capabilities deliberately absent. The request asks for all six — password reset, a named address book, gift delivery to a saved address, filtered order history, a dispatch email, and a wishlist that feeds the basket. One of the six genuinely depends on another, and two of them would both edit the single mail-template registry the repository's own conventions name.

Asked to plan it without building, both hosts produced the decomposition the contract describes.

- Six units, each a capability a person can use end to end, each stated as an outcome with what would show it true. Codex named the anti-pattern itself: "not separate database/service/interface phases".
- One dependency edge, and only one. Both hosts named gift delivery as the only unit that has to wait, and neither invented an ordering edge for the rest. Claude stated the frontier explicitly — units one, four, five and six can run alongside two.
- The shared surface was found without being pointed at. Claude: "I'd just avoid running the dispatch email and gifting at the same time, since they'd both be rewriting the same customer messages."
- Both wrote nothing. A request only to plan records nothing, and neither touched the working tree.
- Both returned the open product questions in one round with recommendations, and named the readings they had taken on their own with the alternatives.

Asked to build it, both hosts did the whole thing in the root context, in one commit, and neither opened `decomposition` or `delegation`. Claude produced 122 new tests, ran the whole member journey end to end against the finished code, named two choices with their alternatives, and left a seventh piece of work as a backlog record rather than widening the change. Codex delivered the same six capabilities against 331 passing tests. Nothing was lost, and each host reconciled all six against the request.

So the split is verified and the orchestration is not. No delegate was spawned, no lane ran concurrently, no worktree was created, no delegate returned a question, and no unit was integrated separately as it landed. This fixture did not reach the size where either host judged delegation worth its cost, and the proportionality rule behaving that way is not a defect. Everything in that list stays `UNVERIFIED`, and no numeric threshold was added to force it.

### A consequential technical decision, and a rule that does not execute

An order service charged the card and called the warehouse partner inside one database transaction, so a partner outage rolled back the order and left the customer charged with nothing to pick. The repository carries the real constraints: one container on one small virtual machine, Postgres as the only stateful dependency, EU-only order data, half a day of engineering a week, a partner that treats the order reference as an idempotency key, publishes a rate limit, and refuses consignments older than fourteen days.

Ten sessions were run on this fixture, five on each host. All ten recovered those constraints, chose the transactional-outbox shape inside the Postgres the project already runs, and introduced no broker, managed queue, vendor, or paid service. None asked the owner to choose a technology; several brought back exactly the choices the repository reserves to the owner, such as capturing the card on dispatch or paying for an alerting service. Claude replayed the eleven-hour outage at documented volume more than once — 1,440 orders in one run, 960 with two container restarts in another, none picked twice — and one such replay caught a real overflow in its own backoff code, which it fixed and covered.

Not one of the ten obtained the outside read from a fresh context that `technical-design` requires for a decision that is expensive to undo. Codex opened `technical-design` in all five of its sessions on this fixture; no Claude session anywhere in the pass opened it at all. Three kernel wordings were written and tested against this fixture and all three were discarded: the read as a condition of finishing, the same with the host's own delegate named, and the same as a step before building on the decision. No run on any of them spawned a delegate, invoked a second runtime, or mentioned the rule, and the two negative controls were re-run under each wording to confirm none of them started asking for reads on ordinary work — none did.

What the runs say points at the trigger rather than the wording. Each treated its own decision as ordinary and cheap to reverse; one listed its remaining choices as "both reversible". "Expensive to undo" is the agent's estimate of its own decision, which is the shape this project has already found unusable once. Nothing was promoted into the kernel, the rule stays in the method unchanged, and the outside read stays `UNVERIFIED`.

### Configured once, and one thing it gets wrong

A project with no tracker and no agent instruction file was given three customer complaints to save. Both hosts asked exactly one question — where the records should live and who may see them — recommended a file in the repository, recorded the answer in the project's own instructions, and wrote the three reports as three separate items because three different repairs would fix them. A fresh session in the same repository then saved two more reports to the same place without asking again, on both hosts. Claude's fresh session also checked the new delivery-estimate report against the previous week's postage report and said in the record why they are separate rather than merging them.

Claude wrote that convention into `CLAUDE.md`, which the other supported host does not read, so a Codex session in the same project would ask the question again. `project-setup` said to use "the project's own agent instruction file" and did not say what to do when the project keeps none. This release closes that gap in wording. Whether the wording changes the behavior is `UNVERIFIED`: the method was open in one of the two Claude sessions that produced the host-specific file and absent in the other, and the outcome was the same both times.

### Which methods load

On Codex, method files load in proportion to the work, and the trigger decides it rather than the size: `technical-design`, `diagnosing-bugs` and `testing` on the architecture case, `decomposition`, `product-decisions`, `codebase-design` and `technical-design` on the request to plan the six-unit build, and none at all on the request to build the same six units, which it read as one pass. On Claude the picture has moved since 2.4.1, which recorded methods opening in one run out of six. Across the twenty-eight Claude sessions whose transcripts this pass retained, all of them on packages at or before 2.4.2 and so before the 2.5.0 clause that made an applicable method non-optional, fourteen opened at least one method — `project-setup`, `intake`, `product-decisions`, `testing`, `decomposition` — and fourteen opened none. No Claude session in the pass opened `technical-design`, including every one on the architecture fixture. The two clauses this release turns on live in the kernel, which is why the cancellation behavior held on Claude in sessions that opened `product-decisions` and in sessions that did not.

A 2026-08-29 scan widened this to every session on the maintainer's own projects that loaded an installed package, using the same method: search each installed reference file's own opening sentence, not its path. The result splits by major version. Under 1.x, twelve of nineteen sessions carried at least one method's text into context — `github` in ten, `delivery` in six, `model-routing` and `long-work` in five each, then `decision`, `diagnosis`, `worktrees`, `engineering`, `intake`. Under 2.x, none of eighteen did, and only one of those touched the package directory at all, to measure the size of the plugin cache. The two heaviest 2.x runs in the period — a triage that opened twenty-two tracker items, and a three-and-a-half-hour run behind twenty-eight delegates — opened none of `tracked-work`, `continuity`, `decomposition`, or `delegation`. The measurement understates loading, because a run that read only part of a file is not counted.

Paired isolated runs on a throwaway fixture do not reproduce that. Four prompts were run on 2.10.1 and again on the 2.11.0 candidate, in a fresh fixture repository per run, with the candidate passed as a session plugin and every setting source dropped; the control run listed the owner skill and the host's own built-ins, and no `CLAUDE.md`, `AGENTS.md`, user skill, or MCP server reached the context, and the transcripts confirm the skill text came from the candidate rather than from the installed package. On both, the matching method opened in three of three sessions and before the run wrote anything: `diagnosing-bugs` on an unexplained defect, `tracked-work` and `project-setup` on a request to record findings without fixing them, `prioritization` on more candidates than could be done soon. The fourth prompt matches no trigger and opened nothing on either. So the failure seen in installed sessions is absent in a clean one, and what causes it is `UNVERIFIED`. The candidate opened one to two more methods per session than 2.10.1 on two of the three prompts, which one run per cell cannot separate from noise. These runs cover the kernel wording; the matching sentence in `decomposition` was tightened after them, and no run in the pass opened that file.

These are observations, not a reliability rate.

### Discovery precision in 2.11.1

The final 2.11.1 selection description was run in nine fresh Claude Code sessions against the exact candidate package as a session plugin. User, project, and local settings were disabled; MCP configuration was strict and empty; each transcript's init event named the candidate as version 2.11.1 and listed no MCP server. The cases are retained as [`tests/skill-discovery-cases.json`](../tests/skill-discovery-cases.json).

- Direct named use, an indirect outcome-owner request, an indirect read-only technical recommendation, and an incomplete checkout defect each selected `skiphow:skiphow`.
- Requests to build an approval workflow or runtime-orchestration capabilities inside the current project also selected it.
- An unrelated explanation, a mandatory owner-operated spec/ticket/TDD/review/approval workflow, and a persistent-agent runtime request each did not select it.

The mandatory-workflow case first exposed a contradiction. With the new description already present but the old startup reminder still saying to load the kernel for every project request, Claude reasoned that the request was for a workflow yet loaded SkipHow because the reminder treated every project request as in scope. After the reminder was changed to defer to the description, the identical prompt did not select the skill. A finishing review then found that excluding those subjects outright would also reject valid requests to build those capabilities in the current product; the final pair of edge cases shows the revised distinction. This is evidence for the corrected Claude selection on one run per cell, not a general precision rate.

Codex discovery on the exact candidate is `UNVERIFIED`. A fresh isolated Codex home has no authentication on this machine, and copying credentials into it is outside this run's authority. Deterministic metadata checks confirm that Codex receives the same description, but they do not prove selection behavior.

### What delegation looked like in installed sessions

The evidence above comes from fixtures, where no run ever spawned a delegate. A 2026-08-29 pass over the maintainer's own installed sessions covers the opposite case. Four sessions on 2.0.2, 2.3.0 and 2.4.1 across two private repositories were read from their host transcripts; two of them dispatched eighteen and eight delegates. Method loading was established by searching each transcript for the method files' own sentences rather than for their paths, because a path can appear in a command without the file's text ever reaching the model.

None of `decomposition`, `delegation` or `execution-health` reached context in any of the four. The longest delegates ran 235, 133, 111, 81, 81, 75, 58 and 47 minutes, and delegates accounted for 67 to 68 per cent of each session's output tokens and 92 to 94 per cent of its cache writes. Twenty-five of the twenty-six delegates the two roots dispatched ran on the session's own model because the host's per-delegate model was left unset; the single explicit downgrade went to a delegate asked to verify a specification against code. One root reported while a lane it had accepted two hours earlier was still running and unmentioned. One created three worktrees beside the repository, against a rule that was in the kernel and therefore in its context.

These sessions are the maintainer's own work, not controlled runs: the package version, repository, and prompt all vary, and nothing here is paired. They are evidence about what reached the model and what the run cost, which is readable from the transcript, and not about whether the wording caused the outcome.

### The delegate methods did not reach the sessions that dispatched delegates

A 2026-09-02 scan read twenty-four installed sessions on the maintainer's own projects, from 2026-08-29 onward and on packages between 2.8.0 and 2.14.0, together with all 102 delegate transcripts beneath them. Twenty-two carried the kernel; fifteen dispatched delegates, ninety-one times at the root and twelve times below it. Method loading was established by searching each transcript for the reference file's own opening sentence, not its path, and the persisted overflow files were swept as well, which changed one session's answer.

Of the fifteen sessions that dispatched delegates, `delegation` was in context before the first spawn in four and `model-routing` in five. `execution-health` reached one of the twenty-four at any point and none before a dispatch. `decomposition` also reached one.

Thirty-one of the ninety-one spawns named no level for the delegate, which on this host inherits the session's. Split by whether the routing text was in context: three of fifty where it was, twenty-eight of forty-one where it was not. One session dispatched twenty-three lanes with twenty-two unrouted and read no method file at all; twenty-one of its twenty-eight delegates ran on the session's model, its longest lane ran 147 minutes, and its delegates consumed 587M cached input tokens, half the delegate total across the whole scan. Another dispatched four read-only verification lanes with no level named, all four on the session's model. In a third the owner interrupted to name `model-routing` by file path; the text reached context eight seconds later and three unrouted delegates too late.

Three requirements the kernel compresses fared worse than the one it does not. A stated completion condition appears in thirty-one of ninety-one briefs and the instruction to return a blocking unknown in thirty-seven, while the delegate's boundary, which the kernel does not summarise, appears in ninety of ninety-one. Twelve briefs in one session handed a single delegate two to five tracker items each, one of them stating that they were strictly sequential. Where the methods did load the briefs met all four requirements: four of four in one session, five of five in another.

No brief in the scan set a duration expectation, and no lane was stopped for exceeding one. Stalls were caught by inspection after a completion notification rather than by a breach: one root found three lanes that had backgrounded their own checks and stopped without committing, diagnosed the pattern and resumed each, at a cost of 106 delegate-minutes plus 22 to redo. One root blocked its own turn twice on a foreground sleep loop, roughly fifty-four minutes with six delegates live and thirty-five per cent of that session's span, and stopped only when the owner said so.

Delegates carried 54 per cent of output tokens and 68 per cent of cached input across the twenty-four sessions, 3,543,563 output against the roots' 3,044,894, and 2,409 delegate-minutes against a delegate-live union near 600, so roughly fourfold parallelism where lanes were used. No delegate transcript contained the kernel or any method text, and none of the 210 `Skill` calls delegates made anywhere in the tree named the owner skill. Twelve delegates dispatched delegates of their own, to a maximum of two levels below the root, all of them as ordinary agents.

These are the maintainer's own sessions, not controlled runs: version, repository and prompt all vary, and nothing is paired. They measure what reached the model and what the run cost. They do not show that the old wording caused the outcome, and the counts are an upper bound on conformance because a rule the run noticed and dropped leaves no trace.

### Paired runs on 2.15.0 did not reproduce the delegate loading failure, or fix it

Six isolated sessions ran on a throwaway five-defect fixture, three on 2.14.0 and three on the 2.15.0 candidate, in a fresh copy of the fixture per run, with the package passed as a session plugin and every setting source dropped. A first prompt that described five independent defects and asked for them in parallel produced no delegate in any of the six runs, on either package, and all six fixed the defects directly. A second prompt that named parallel lanes explicitly produced five delegates in every run on both packages.

In those six dispatching runs, all thirty spawns named no level for the delegate, and no run on either package opened `delegation`, the routing text, or `execution-health`. The kernel loaded in every run. So the reworded method-list line did not fire in a clean session, exactly as 2.11.0's fixture runs failed to reproduce the loading failure they were built for, and this fixture does not discriminate between the packages.

That result is why the kernel keeps one obligation at the point of use rather than relying on the method list alone. It is evidence against the sufficiency of the trigger rewrite and not evidence for it, and the pass reports it as such. The fixture is small, the sessions are short, and one prompt per cell separates nothing from noise.

### The kernel obligation reached the method where the method list did not

Three further sessions ran on the released 2.15.0 tree, on the same fixture, prompt, host, and session model as the six above. That package differs from the candidate arm in exactly one file: `SKILL.md` carries the obligation to read `delegation` before dispatching a delegate.

`delegation` was in context before the first spawn in two of the three runs, and in both of the two that selected the skill at all; the third never loaded the kernel, which is the discovery variance one run per cell cannot separate from noise. The candidate arm was zero of three with the skill loaded in all three. Five of the fifteen spawns named a level, against none in either earlier arm.

The run that read the method and still named no level is the useful one. It opened `delegation`, made the routing judgment explicitly, and wrote in its own message that each lane would run "at ordinary level (bounded fix against a stated test spec)". It then passed no level in any of the five dispatches. It also placed all five lanes in one checkout, reasoning that no two touched the same file, with the isolation rule in context. So the obligation is shown to get the file opened, and opening the file is not shown to produce either the routing or the isolation. The first is a property of the text and three runs can support it; the second is a run deviating from text that was plain and in context, which no number of sessions this small can generalize.

Three more sessions ran the same way on the shipped 2.15.1 tree, which adds the readability pass and the two completed scope lines. All three loaded the skill, all three opened `delegation` before the first spawn, and all fifteen spawns named a level, every one of them the cheapest available. Read as a non-regression check on the readability pass, that is what it is. Read as a claim that structure caused the difference from 2.15.0's two of three and five of fifteen, it is three runs per arm against a difference of one run, and the pass does not make that claim.

`execution-health` opened in none of the twelve runs. Its trigger names a step that could take real time, and nothing in a five-defect fixture is one.

### Plan mode does not explain the unread methods

The 2026-09-02 audit of two installed CI-cost sessions proposed one competitor to the kernel's at-the-act delegation obligation: both sessions started in plan mode, whose host reminder opens by telling the run to launch up to three Explore agents in parallel and to use only that agent type. That is an instruction to dispatch, with the agent type already chosen, before anything else. This pass tested it.

Eleven isolated sessions ran the deciding pair on exact unmodified `v2.16.0`, host 2.1.259, a fresh throwaway fixture per run, `--setting-sources ''` with `--strict-mcp-config` and the package passed as a session plugin. Six ran with `--permission-mode plan` and were then resumed in the same session with an ordinary approval, because a headless plan-mode session ends at the plan and the field shape is plan, approval, execution; five ran without it. Nothing else differed. Five of the eleven carried a per-session spending limit; the other six were the unbudgeted first pass and agree with them line for line. Every one confirmed the candidate from its own transcript by the base directory the skill itself reports, and a control run with no package listed the host's own built-ins, carried no kernel text and no method text, and showed no trace of the maintainer's own instruction files.

On the fixture whose triggers plainly match, the two arms are the same. All eleven loaded the kernel and all eleven opened `delegation` before their first spawn, and every spawn named a level: forty-nine of forty-nine with plan mode and forty of forty without. Levels were routed across two models rather than inherited. The one asymmetry runs the wrong way for the hypothesis. `execution-health` opened in four of the six plan-mode sessions and in none of the five without, its first appearance in any fixture run, so plan mode read more of the package rather than less.

So plan mode does not do this on its own. The installed sessions it was proposed to explain opened no method in one case and `research` alone in the other, and none of their nine spawns was preceded by `delegation`. The same package, in a clean session, opens it every time on both arms. What the pair cannot do is rule plan mode out as one term in an interaction, because the clean fixture never reproduced the failure for it to interact with; a receipt that finds no difference between two arms bounds the size of a sole cause, not of a contributing one. Either way the difference belongs to something long installed sessions carry rather than to the wording, which is what the record already held. The cause stays `UNVERIFIED`.

The negative results are worth as much as the pairing. Twenty sessions on a documentation-reconciliation fixture, in three sizes, opened a method in three of them, `project-setup` and `tracked-work` and never `delegation`, and dispatched one delegate between them, because a templated docs set is reconciled by writing one script and every run said so in its own words before doing it. Six more on an eight-defect service opened `diagnosing-bugs` and `testing` and delegated nothing. So one delegate appeared across those twenty-six sessions against eight or nine in every session on the prompt that named parallel lanes. That is consistent with the prompt shape the 2.15.0 pass recorded without establishing it as the necessary condition. A fixture that does not reach the size or shape where delegation earns its cost measures nothing about delegation, and the proportionality rule behaving that way is not a defect.

Two limits belong with the numbers. The kernel's own text did not reach three of the twenty documentation sessions, so a run counts only when its transcript confirms the package rather than because the flags were right. And disabling every setting source keeps the maintainer's own instruction files out of a session's context but does not stop the session from reading them: one run, voided for a separate reason, read the host's own user-level instruction file by hand fifteen seconds in and followed the import it found. That run was voided because two concurrent processes shared its fixture directory and its log file, each destroying the other's evidence, which is why every run now gets its own.

The pass cost forty sessions across fifty-one invocations, $165 and nearly five hours to settle one yes-or-no question, and the four sessions that carried the answer cost under six dollars between them. Three fixture redesigns produced no delegate at all before the prompt named parallel lanes, which the record already said, and letting the delegating runs finish added most of the remaining cost without touching the observable, which lands at the first dispatch. `AGENTS.md` now bounds a receipt accordingly.

### One rule with two homes had already drifted

Version 2.16.0 compared every sentence of seven words or more in the kernel and the twenty-three methods against every other, 865 sentences and 373,680 pairs, ranked by shared vocabulary. Forty-nine pairs passed the threshold and four were one rule with two homes. Of the remaining forty-five, nineteen pair a method-list trigger with the scope line that repeats it, thirteen pair a kernel invariant with the technique beneath it, and thirteen are two methods stating adjacent rules in their own terms.

One of the five had already drifted, which is the evidence for the rule rather than an argument for it. `tracked-work` said an item the code has already overtaken is reported as done rather than redone; `advancing-tracked-work` said it closes as done rather than being rebuilt. Reporting and closing are different acts, and closing needs a write grant that reporting does not. Nobody edited both.

A fifth, the regression-observation rule stated twice inside `testing` under two different qualifiers, scored below the threshold because the two statements share almost no vocabulary. It was found by reading. That is the measured limit of the scan: it finds repetition, not restatement.

### Long installed runs kept waking without new evidence

A 2026-08-30 audit examined four large installed Codex task trees from the maintainer's own projects. The three largest roots made 1,785 delegate wait calls. Of those, 855 expired with an explicit timeout and no mailbox activity. For two roots, each timeout was joined by call identifier to its result and then to the next model turn, with any interval containing another message excluded. All 472 unchanged timeouts qualified. The following turns processed 62,931,387 input tokens, 62,568,704 of them cached. This is repeated context traffic, not unique tokens. Six root compactions occurred across roughly 43 hours, so the larger repeated cost was waking and reprocessing a large root context rather than compaction itself.

The methods did reach these runs. `execution-health` told each root to set a healthy expectation and recognize a breach, but it did not say when a healthy lane should next reach the root or that an unchanged bounded wait was not evidence. Version 2.12.0 fills that gap inside the focused method. It prefers host events or waits, keys observation to facts that can change the next action, and says to renew an unchanged bounded wait without another inspection or reasoning pass. It names no host command, polling interval, model, role, or persistent state. Whether this reduces context traffic in a later run is `UNVERIFIED`; these are uncontrolled observations, not a before-and-after receipt.

The same audit found a separate reconciliation failure. One task created 32 worktrees while its delegated units landed and were integrated. It issued no worktree removal or prune command and reported completion without disclosing the remaining working state, although `finishing-a-branch` had reached context. Version 2.12.0 does not duplicate that method's cleanup rules or move them into the kernel. It makes the root's existing named-end reconciliation include the branch and isolated checkout a unit created, links the authoritative method at that point, and forbids calling the delegated set finished while integrated working state remains unaccounted for. Whether that point-of-use restatement prevents accumulation is `UNVERIFIED`.

### A permitted question, put in the wrong language

An installed 2.10.0 session on a real project spent two hours fixing a defect end to end, then closed by asking its owner two things. One was a payment setting inside the owner's own account that no agent can reach, and it drew no objection. The other asked whether the run might replace a named environment variable on staging with the currently authorized GitHub CLI token, offered against a properly scoped token the same sentence called better. The owner rejected that one as a question that was never theirs.

The classification was right and the wording was not. Substituting a credential is an action the kernel reserves to the owner's grant, and the run applied that deliberately: an hour before it asked, it said it would not substitute the credential without a separate permission, while making the staging configuration change beside it without asking, because the owner's request had named staging and had not named credentials. But asking for a grant is not asking the owner to pick a mechanism, and the sentence forbidding the second was in the kernel and in context all session. The run's reasoning never reaches it. Told the decision was its own, the run named the same defect the owner had, the phrasing rather than the ask, and finished the delivery within the hour.

This is a run deviating from text that was plain and in context, which one session can never generalize. The count is one: every session on both hosts that loaded the package in a real project was scanned for a question of this shape, this is the only one, and the only other permission-shaped question was a legitimate product question about what a public ranking may reveal. Six methods loaded in that session and none of the three carrying adjacent guidance was among them, which follows from their triggers rather than from a failure to open them. What 2.10.1 changes is where the existing rule is stated, not what it requires, and it is recorded in [`docs/decisions.md`](decisions.md) as the owner's decision against an unmet bar. Whether it changes what a run writes is `UNVERIFIED`, and no paired receipt was made.

### Two sessions in one checkout, and an isolation that reported success

A 2026-08-27 session on 2.1.2 in one of the maintainer's private repositories dispatched two delegates through the host's own worktree isolation. The host placed both in the shared main checkout. The root saw only a symptom — the base commit was not the one its brief named — read it as the worktree having branched from the wrong ref, and instructed a delegate to reset hard to that base, reasoning in the message it sent that the delegate had changed no files and so the reset would discard nothing. That reasoning is sound in a worktree of its own. In the shared checkout it destroyed thirteen files of uncommitted work belonging to a second session that was writing the same tree at the same time, and that session recorded the loss independently as its own edits reverting on disk. The work came back only because the repository's commit hook had stashed a patch of unstaged files minutes earlier. The two sessions then reconciled ownership of the changes by messaging each other.

Concurrency of this kind is the maintainer's ordinary mode rather than an accident: in that one repository, twenty-six pairs of sessions that both ran writing commands overlap in time across six weeks, and eleven separate requests between 2026-07-04 and 2026-08-29, across four repositories and at least three of them addressed to this package, carry a hand-written instruction that another agent is running and that the session should avoid conflicting with it.

The failure is not that isolation was missing. It was requested and the mechanism reported success. The package that ran carried no worktree guidance in `delegation` at all — the sentence preferring the host's own mechanism arrived the next day in 2.2.1 — so this run is evidence of the failure mode and its cost rather than of that sentence causing it. What the current text adds to the record is that the sentence arrived, and still arrives, with nothing asking a run to confirm what the mechanism handed back. The same shape is documented upstream in projects that solved isolation earlier: worktrees silently degrading to the shared tree under a condition their own base check created, and session-scoped isolation disabled for a release by one wrong environment variable name with no symptom.

One fact behind the second half of that clause was tested here rather than taken from a source. Two worktrees of one repository share a single stash stack: a stash pushed from either is listed by both, and a pop takes the top entry whichever tree created it. Git 2.50.1.

### One genuine compaction selected the wrong continuation store

One installed Codex session running SkipHow 2.11.1 reached a genuine context compaction. The host delivered the package's `compact|resume` hook output as a developer message. That output told the agent to inspect `.skiphow/handoff.md` if it existed. The agent repeated that instruction in its next update, then included a direct probe for the path in its first live-state read. The project already kept the active work in its own records, and the probe returned no handoff content.

This is one whole-session observation. It proves that the package wording caused the probe because the wording reached the agent as a developer message and its next two actions followed it. It does not show that agents generally mishandle continuation, and it says nothing against the fallback itself. The focused method allows the file only where a project has no tracked-work destination. [Issue #79](https://github.com/mzored/SkipHow/issues/79) records the fix: the always-loaded reminder stops selecting a store, while the focused method keeps the conditional fallback. That guidance now sits in `tracked-work`.

### Long campaigns can keep moving after their direction has gone stale

Two owner-requested read-only audits ran in private real-project sessions carrying installed SkipHow 2.12.0. The first found a six-day period dominated by repair and test work, high concurrent work in progress, duplicated findings, a custom release supervisor that had become its own defect source, and parallel implementations of the same business transitions. The second found application code up by roughly half, tests up by more than four fifths, and workflow code up by more than one and a half times over a two-week baseline while the main production journey remained unproved. A release candidate there had already met its stated performance target before roughly 2,400 more lines of cold-cache certification and admission machinery were added.

The audits show the condition and its cost. They do not show which package version governed every earlier session that produced it, whether the relevant methods reached those sessions, or whether plain instructions were ignored. Those historical causes stay `UNVERIFIED`.

The 2.12.1 text has a demonstrable gap independent of that history. `technical-design` carries the reuse order, `codebase-design` carries the deletion test, `execution-health` recognizes lane anomalies, and tracked-work reconciliation checks individual items. No reached rule owns the direction shared by a complete multi-unit plan or an ordered campaign when aggregate repair, process growth, and missing product evidence contradict it. Version 2.13.0 adds that check at decomposition, multi-item continuation, and work-stream anomaly boundaries.

Five read-only fixtures were run as matched 2.12.1 and first-candidate pairs on Claude Code 2.1.251 with the same prompt and repository state. Claude reported `claude-opus-5` in every valid session. The runs disabled every setting source, used a strict empty MCP configuration, and passed one package as the session plugin. Each init event named only the baseline or candidate plugin path and the host's built-ins. Three fixtures carried a stale direction: a release runner growing after its target had passed, repeated repairs across three definitions of payment state, and eight nominally ready repairs outrunning a one-integration-plus-one-review limit. Two controls carried justified refund recovery work and three healthy product slices.

The first candidate opened `campaign-direction` in all three stale-direction fixtures. It also opened the method for the refund work because that work extended shared payment machinery, then kept the direction after finding no repair chain, competing path, sibling invalidation, or unsupported growth. It did not open the method for the healthy product slices. In the capacity fixture it admitted one repair lane and one review lane, collapsed two records with one cause, and declined the remaining fan-out. In the duplicate-state fixture it chose one canonical payment truth and retired the compatibility direction. In the release-runner fixture it retired the unsupported cold-cache work and kept the maintained CI comparison behind one current baseline run.

The baseline also challenged the direction in all three positive fixtures, including the same capacity limit and payment consolidation. The pairs proved the first trigger reachable, but did not justify making every new shared mechanism pay for the method. Review rejected that trigger and the added decomposition gate. A later five-session candidate required an observed direction signal instead. The three stale fixtures opened the method; refund recovery and healthy product slices did not. That candidate differs from the released package only in the later clarification of the existing product-choice boundary.

The candidate revisions also exposed an authority leak. Results made the technical decision themselves but invited the owner to overrule the retired runner work, restore a separate recovery-test item, or request optimistic crediting instead. A campaign-only sentence could not fix the last case because the corrected trigger rightly left that method closed. The released package therefore states the report boundary in the kernel and limits the owner's reversal right to product choices. The release-runner and refund fixtures were repeated on that exact package. Neither returned a technical alternative for ratification or reversal. The refund result named one reading about when a customer's balance changes as a product choice, which is the owner's boundary.

No Codex behavior receipt was accepted. A fresh operating-system home and `CODEX_HOME` correctly reported no login, and device authorization required a human account action. The attempt was cancelled rather than copying credentials from the maintainer's normal profile or weakening the isolation. Codex behavior for this change stays `UNVERIFIED`.

### A proposal became takeable without becoming accepted

One linked dogfood incident crossed three private real-project sessions carrying SkipHow 2.12.0 and 2.12.1. A read-only audit found competing implementations of a maintained capability that the owner's current product description did not mention, and recommended consolidating them. A second session converted that recommendation into takeable tracked work. A third session executed it. The owner later challenged the direction and clarified that the capability was not part of the future product.

The chain shows two things. The contract allowed project artifacts to settle a product reading without distinguishing current state, a proposal, and an accepted owner decision. Its point-of-use coverage also failed: the planning session reached `tracked-work` but not `product-decisions`, so a correction confined to the latter would not have governed the promotion into actionable work. The three sessions are one observation, not three reproductions, and the private transcripts are not retained in the repository.

Version 2.13.1 puts the distinction in the always-loaded kernel, clarifies it in `product-decisions`, and preserves source decision status in `tracked-work`.

A throwaway repository then held two audit findings: a reservation-integrity defect covered by its authoritative product brief, and partner-export consolidation absent from that brief. The prompt asked Claude Code to turn the audit into a backlog and launch brief without changing code. Settings sources and MCP servers were disabled, session persistence was disabled, the fixture and package paths were explicit, and the init event identified Claude Code 2.1.251, Sonnet 5, and the exact inline package. The exact 2.13.0 package loaded the skill and made both findings `Ready` with no open product question.

Candidate 2.13.1 runs exposed useful boundaries rather than a clean pass. The first kept both findings proposed and deferred the question, so the contract learned to trust an authoritative brief for accepted scope and to ask an already askable question in the current result. A second correctly made the core repair `Ready` and the export work non-takeable, but framed the blocker as a technical contract choice for a partner owner, so the contract learned to ask whether the capability belongs rather than how to implement it. A later loaded run made the core repair `Ready` and the export work `Proposed`, but still omitted the owner question. After the final narrow kernel wording, an exact-package repeat did not load the skill and made both findings `Ready`; it measures activation failure, not compliance with text the model never read. An earlier permission-denied attempt was discarded rather than counted.

The receipts show that the old package allowed the promotion and that loaded candidate wording can preserve the distinction, but not that the complete behavior is reliable. Claude behavior remains `UNVERIFIED`; no Codex behavior run was accepted.

### A campaign kept building after its result came to wait on the owner

Three owner-run installed Codex Desktop sessions over 2026-08-31 and 2026-09-01 were read from the host's own transcripts for this change, with per-message usage and timestamps. The transcripts are private and are not retained here.

The first asked the run to close the tasks blocking first payments and real traffic, granted production, and asked for human-only steps to be batched. It ran 36.8 hours, spawned 61 delegates, issued 1,784 delegate waits, and processed 137 million input tokens, 99 per cent cached. The 2.13.0 kernel governed from the start and the 2.13.1 kernel reached its context at hour 22. Its two genuine blockers, a public OAuth defect and a receipt-contact rule, were integrated by hour 17. From hour one it also admitted a backup-recovery item, in its own words to use free capacity, thirty minutes after it had computed the money path without that item; the item's "before traffic" premise came from an audit finding recorded two weeks earlier. That lineage then produced eight tracker items, each new one written as a prerequisite for resuming the last, four independent reviews, three architectures, and about 1,700 uncommitted lines when the owner returned and paused it. `campaign-direction` was opened in context three times and each pass replaced the architecture. Fifteen hours of that followed the 2.13.1 wording. A fresh session the next day, asked by the owner why it had taken so long, answered in ten minutes that the lineage protected a CI proof of disaster recovery rather than the product, and proposed a plan whose first item was the one human step the run had asked for at minute thirty-five.

The second asked the run to exhaust the takeable internal frontier of a tracker that an earlier session had built from a complexity audit. It ran 22.9 hours as one orchestrator with forked delegates and closed twelve items: CI routing, size budgets, evidence packaging, Markdown tooling, benchmark isolation. The audit those items came from had said the evidence system was the excess and that a device test with real people, recorded as a human-gated item, was the most important next step. A fresh session the next day, asked whether there was anything to play yet, counted 75 commits and roughly 9,800 lines since the audit with no new game behavior.

The third asked for reproducible bugs and staging blockers on one campaign, then a staging release. It ran 8.2 hours, mostly on the project's own release gate and two flaky tests, released to staging, and the owner checked staging the next morning and accepted it. It shows a scoped request staying scoped, and nothing else.

Counted in whole sessions: one shows drift from the stated result under the shipped text, and shows the 2.13.1 kernel in context and not stopping it. The second complied with its request as written, because the request named the frontier itself as the result; what it shows is a request of that shape producing a day of tooling with no product evidence and no sentence in the package that would make the run say so or ask whether to continue. The transcripts show the per-lane rules of `execution-health` being applied throughout, twenty-minute checkpoints and three-attempt stops included; what no text supplied was a measure of the remaining takeable work against the owner's result once that result waited on the owner. The wording defects are readable in the files and are listed in the changelog and decision history.

Version 2.14.0 bounds the frontier by the result, adds defer as a direction outcome, deletes the recovery exemption, extends the provenance rule to sequencing claims and to the run's own records, and names prerequisite-spawning as a signal.

One matched Claude Code pair was then run on a throwaway shop repository whose tracker held two takeable items on the payment path, one human-gated item on it, and two audit-derived infrastructure items off it, with the same Get5Stars-shaped prompt, settings sources and MCP disabled, the package passed as a session plugin, and the init event naming Claude Code 2.1.258, Opus 5, and the exact package path each time. Exact 2.13.1 and the candidate both did the same thing in about five minutes: closed the two path items, continued past the human gate rather than stopping at it, found that the payment adapter never charged anything and recorded that as the real blocker, marked both audit items proposed, put the backups-before-money question to the owner as a risk choice with a recommendation, and stopped with one batch. Both opened the frontier method. The pair shows that the new wording keeps a run moving through a human gate and does not add a question or a gate; it does not show the improvement, because the released text already behaved correctly on a five-minute fixture, as the 2.13.0 pairs also found. What the installed campaigns show and the fixture cannot is a run twenty hours in, holding records it wrote itself, with free delegate capacity and nothing left on the path.

## 4.x encoded Contract

What the current package's text requires, settled by reading it. Nothing here has a run behind it. The sentences live in [`SKILL.md`](../plugins/skiphow/skills/skiphow/SKILL.md) and its eight conditional playbooks.

- One accountable virtual CTO owns the technical lifecycle through current-state inspection, research, architecture, planning, implementation, review, integration, verification, and operational learning. Technique stays proportional; no fixed stages, role counts, or private runtime are required.
- Before consequential work it reconciles the request with live product, code, tests, Git, branches, worktrees, records, CI, and host state. It compares repository and platform capabilities, official integrations, maintained open source, managed services, bounded experiments, and custom code where relevant.
- Programmes split into observable end-to-end outcomes with real dependency edges. Existing authorized tracking is used when work has several deliverables, spans sessions or writers, needs a durable decision, or leaves a separable material defect; tiny same-session work gets no ceremony.
- Models and effort are configured deliberately for the actual task. Every change gets review scaled to consequence, with an independent read for substantive or high-risk work. Process and environment failures are diagnosed at their own root cause rather than converted into product changes.

- Authority comes from the owner's messages and trusted host-, user-, organization-, or administrator-managed policy. Repository instruction files are applicable project procedure within authority already granted, evidence until their provenance is established in an untrusted revision, and never a grant of mutation, secret access, disclosure, network egress, permission change, cleanup, or protected external effect. Records the owner points at authorize pursuing the outcome, and stay untrusted task data.
- A read-only request writes nothing. A change request grants in-scope local edits and non-destructive validation, and may include a clean local commit of owned changes when the commit path is known not to cross another boundary; otherwise the work stays uncommitted with the reason stated, and that is not implementation failure.
- Protected actions need an exact grant. Broad autonomy language, project procedure, issue text, and tool capability do not supply one.
- Product consequences are the owner's; engineering mechanics are the agent's. One outcome-level question, independent work continues, dependent behavior waits.
- Foreign work is preserved. Delegates are read-only without verified distinct isolation, and the root serializes writes. A delegate's surface is a boundary on its authority, not a plan; its model and effort are chosen for the task's consequence and complexity rather than by a fixed tier or a floor at the session's own level, and naming a level in the root's own message does not set it.
- A read-only review reports confirmed defects and modifies nothing; urgency, including a security finding, does not widen the request, and a sensitive finding stays private without a disclosure grant. Repair happens only when it was authorized.
- A step that could take real time gets an expectation of healthy progress, and a breach is information rather than a reason to wait longer; monitoring prefers the host's own wait mechanism to a loop that holds the turn.
- Reuse is a presumption, not a law: a maintained capability is preferred to custom code where it fits, and a disposable experiment is cheap to run and cheap to discard, its shortcuts never becoming architecture by staying in place.
- A test is the narrowest stable one that would catch the real defect; mocks and seams appear where they materially improve isolation, determinism, cost, or safety, without asserting call order or private state.
- Completion is relative to the authorized destination: a local branch with no granted destination can be complete, a named destination is incomplete until verified there, and no historical convention grants a push or a review. Earlier-run artifacts are not cleaned under an unrelated change.
- Every requested part is reconciled before success is reported; a simulation is never described as an external effect; a check that did not run is not a check that passed.

Whether any of that changes what a model does is the next section's question, and that section is empty.

## 3.x and 4.x Observed behavior

None. No run has been made on any 3.x or 4.x package. Every current behavioral claim is `UNVERIFIED`; the release ships on reasoning about the text and deterministic checks that start no model.

## UNVERIFIED comparisons and capabilities

- Whether the 2.14.0 frontier bound and defer outcome stop a long run when its result waits on the owner and only enabling work remains. One installed 2.13.0 campaign shows the drift with the 2.13.1 text in context, and a matched five-minute pair shows both packages already behaving correctly at that scale, so the fixture is not where the defect lives. The line closes only on the owner's next long installed campaign.
- The outside read of a consequential design decision, as a rule, is gone. Ten runs made the decision well and none took an outside read; Codex had the method open in all five of its runs, no Claude session in the pass opened it at all, and three kernel wordings changed nothing on either host. Version 3.0.0 removed the mandatory read rather than reword it a fourth time, and removed the broad mandatory outside review with it; review is now scaled to the risk in front of the run. What is still open is narrower than the old line: whether a run scales review up and gets a read taken from a context that did not produce the decision, at a boundary that genuinely warrants one. Nothing measures that.
- Delegation under the shipped wording. The detailed position lives here; public summaries preserve its version and limits. Controlled isolated runs do spawn delegates, and have since 2.15.0. Thirty spawns across the six dispatching runs of the 2.15.0 pair, fifteen on the released 2.15.0 tree, fifteen on 2.15.1, and eighty-nine across the eleven sessions of the plan-mode pass on exact `v2.16.0`. What no controlled run has demonstrated is the rest of it: no lane ran concurrently in a verified isolated checkout, no worktree was created, no unit was integrated separately as it landed, and one run placed all five of its lanes in a single checkout with the isolation rule in context. Delegation as an act is observed; delegation as this project describes it is not. The installed sessions above show delegation happening at scale but with the governing methods absent from context, so they say what delegation costs and not whether the wording works. The 2.15.0 kernel obligation is now measured to get `delegation` opened before the first dispatch, and one of those runs read it and routed nothing anyway. Whether the method's own rules hold once it is open is unmeasured. The lane-health guidance first reached a fixture run in the 2.16.1 plan-mode pass, as `execution-health`; it now sits inside `diagnosis`, and whether it changes a run is still unmeasured.
- Whether the 2.12.0 observation rule reduces root context traffic or the reconciliation rule prevents integrated working state from accumulating. Both changes answer installed failures, but neither has run in a comparable session.
- Whether a rule moved into the kernel is followed. The installed sessions carried the kernel's worktree-placement rule and one breached it anyway, so kernel placement is shown to change what is read and not yet what is done.
- Whether routing a delegate down is cheaper in total rather than per token. No paired run measures it. What the 2026-09-02 scan adds is the cost of naming no level at all, which is not the same question.
- Whether the second round is reliable on Codex. It happened in one of three released-package sessions on the cancellation fixture, and in the shared-basket pair before it. When it does happen, nothing gets built, which is the part this release adds.
- Whether the corrected setup wording puts the setup record somewhere both hosts read. That wording now sits in `tracked-work`.
- The tracked-work lifecycle 2.8.0 put in the kernel was removed in 3.0.0, and no run was ever made on it. Whether work carried on a review branch acquired an item before that branch, whether the item was claimed before investigation, and whether linked closure was wired at branch creation rather than left to a later session went unmeasured for the whole life of the rule, from 2.8.0 to 2.16.1. It shipped on the owner's decision alone, never met the evidence bar `AGENTS.md` sets for a mandatory step, and cost nothing to remove because nothing had ever shown it doing anything. It is the clearest case in this file of a mandatory rule that no receipt supported at any point. Nothing about it remains open.
- The design triggers rewritten in 2.10.0. What is measured is the old trigger failing: no Claude session in the pass opened `technical-design`, including every session on its own architecture fixture, and none of the ten runs there took the outside read because each judged its own decision cheap to reverse. Whether keying the trigger to what the project holds gets the file opened, and whether the greenfield paragraph produces the question, are both unmeasured. So is the survey case, which now sits inside `technical-design`: no run has been made on a request to improve an existing structure.
- Whether the concurrency wording added in 2.9.0 changes what a run does. The failure it answers is on record and reproducible in its own terms, but no paired run has been made on the new text, and no receipt shows a session avoiding a peer's work because the kernel told it to rather than because the owner did.
- Whether the 2.10.1 phrasing rule for a protected or human-only ask changes what a run writes. It restates a rule that was already shipped and already in context when one installed session broke it, so there is no gap in the text for it to close and no receipt that repeating the rule closer to the decision helps. It is the owner's decision, recorded as one.
- Whether 2.13.1 reliably preserves product-intent provenance and asks the product question. A matched Claude fixture showed exact 2.13.0 promoting both findings and loaded candidate wording preserving the disputed item as proposed, but the candidates did not reliably ask and one exact-package repeat never loaded the skill. No Codex behavior receipt was accepted.
- Whether removing the disclose-afterwards wording changes anything. The escape it left was observed; its removal was not run.
- What makes methods go unread in long installed sessions. Eighteen 2.x sessions opened none and twelve of nineteen 1.x sessions opened at least one, but the paired isolated runs load them reliably on both packages, so the difference belongs to something those sessions carry rather than to the wording 2.11.0 changed. Plan mode was the one named candidate and is now refuted: forty-one isolated sessions on exact `v2.16.0` behave the same with it and without it, three of three opening `delegation` before the first spawn on both arms. Whether removing the permission that contradicted the loading rule changes what a long session does is still unmeasured, and no other candidate has been named.
- Whether the corrected plan destination puts a plan in the tracker. One installed session wrote a multi-unit plan and a launch brief to ignored local files under the old condition; no run has been made on the new one.
- Stopping after three genuine attempts against one hypothesis. The fixed count was removed in 3.0.0; stopping is keyed to whether another attempt would produce new evidence, which is what the intermittent-failure run actually demonstrated. No receipt ever supported the number itself. What stays open is whether the evidence-based wording stops a run at a point the count would not have.
- Whether the asking rule over-asks in general. Sixteen negative-control sessions are a counterweight, not a bound.
- Continuity under the corrected compaction reminder. The installed 2.11.1 session above proves that the old reminder caused an unnecessary handoff probe. No genuine compaction has run on the corrected package, so whether reloading the kernel leads the agent to the right continuation source remains `UNVERIFIED`. A simulated compaction would not settle it.
- Whether the 2.13.0 direction checks change a real campaign whose repair, integration, or process load is growing without new evidence of the owner's outcome. The Claude fixtures show the method loading and the intended judgments, but 2.12.1 made the same central judgments, no run had live lanes to stop or records it was allowed to rewrite, and Codex has no accepted receipt.
- Whether the 4.0 virtual-CTO contract changes model behavior at all. No receipt compares it with 3.0.1 or a base host. The release ships on reasoning about the text and deterministic checks that start no model.
- Whether removing mandatory method routing changes what a run opens. Every loading number in this file was measured against a package that told a run an applicable method was not optional. Consulting guidance where uncertainty, risk, duration, an observed failure, or a repository requirement makes it materially useful is a weaker instruction than that, and no run has been made on it. Fewer methods opening is the expected result rather than a defect, and neither direction is measured.
- Whether the read-only delegate default and the verified-isolation precondition are honored. The failures they answer are on record: one run put five lanes in a single checkout with the isolation rule in context, and one host worktree mechanism reported success into the shared tree and cost thirteen files of a peer session's work. The new default reverses what those runs did. No run has been made on it, and a rule moved or strengthened has been shown before to change what is read rather than what is done.
- Whether a genuinely compacted or resumed governed session reconstructs the outcome, authority, live state, and still-valid evidence without the removed reminder hook. A simulated compaction would not settle it.
- Real production or public-delivery actions.
- Comparative cost or speed against any other approach. Nothing here benchmarks SkipHow against anything.
- Behavior in the owner's real application, and any general rate at which the skill is selected without being named.
- Every 3.x contract correction retained by 4.0: provenance-aware authority, records as untrusted task data, the repository commit-hook boundary, read-only review that never becomes repair, destination-relative completion, no earlier-run cleanup, and read-only delegates without verified isolation. The 2.x observations above show failures some answer; none shows current wording doing anything.
- Activation itself. Explicit invocation, native implicit discovery, and the reversible persistent-instruction setup have no 4.0 receipt against a base host. Documented host loading is not automatic-selection evidence, so no activation mode is called reliable.

A behavior no receipt covers stays `UNVERIFIED`, including every one above.
