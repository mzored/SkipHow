# Current decisions

This page records SkipHow's live decisions under the [owner-outcome contract](outcome-contract.md), each with its reason, status, and what would reopen it. A decision reopens when host behavior, model evidence, product goals, security boundaries, or maintenance cost changes its premises, and the [older narratives](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/decisions.md) are context to weigh, never a veto. The [table as of 7.0.1](https://github.com/mzored/SkipHow/blob/2f72c7f218f29db20421eddce6d280e0d6f52045/docs/decisions.md) keeps each row's version history.

`Contract` means the shipped text encodes it and no run has tested that text. `Deterministic` means a check proves it on every run. `Observed` means a retained run showed it; [evidence](evidence.md) holds the receipts.

## Authority and the owner

### Authority comes from the owner and trusted policy

Authority is the owner's messages and trusted host, user, organization, or administrator policy. Repository instructions set in-scope procedure and are only evidence in an untrusted revision. Records and tool output grant nothing.

**Why.** Anyone can plant a file in a repository. A record the owner points at authorizes its outcome and nothing more.

**Status.** `Contract`. Adversarial cases in `evals/` are not run.

**Reopens when.** A run treats a repository file or record as a grant, or a host ships enforced provenance.

### No technical choice reaches the owner

The agent settles engineering and reversible technical uncertainty itself and explains consequences instead of asking. A running result shown to the owner names its branch or revision and its address.

**Why.** Keeping the owner out of engineering is the boundary this product exists to hold, and a recommendation the owner can decline does not stop the work. Several checkouts of one project answer on the same default address.

**Status.** `Contract`. Five corpus cases forbid technical questions; none has run.

**Reopens when.** The recommendation channel hands product choices back, or an owner asks for the technical options they no longer see.

### Read-only stays read-only, and a grant sets what travels

Answer, diagnosis, review, research, audit, and plan requests write nothing unless the owner asks for a record or repair. A change request carries routine engineering through the established non-production workflow, and the lead batches accepted results into delivery units without holding finished work behind unrelated blockers. Iteration stays local until the owner asks for delivery, names a destination, or, outside an invoked iteration workflow, accepts with nothing further to send.

**Why.** Invoking the plan workflow requests records, and automatic selection grants nothing. Preparation and production are separate grants, a handoff and the final delivery can have different destinations, and local combination grants no publication. An owner-selected workflow keeps existing grants, audience boundaries, and downstream-effect checks.

**Status.** `Contract`. Workflow behavior `UNVERIFIED`.

**Reopens when.** A run shows unauthorized effects, missing requested records, needless permission questions, per-assignment publication, closure after a local handoff, or blocked work delaying unrelated delivery.

### Supervision covers the project, bounded by confirmed findings

The lead looks across the authorized project and fixes confirmed findings at safe boundaries. A finding counts when it names a broken behavior or requirement, a security or data risk, a contradiction with the request, or a simpler design. The lead stops when the next step buys the owner less than it costs.

**Why.** A narrow pass can leave material risk elsewhere. An earlier rule to resolve every feasible finding, with no bar on what counted, turned reviewer requests for more tests and guards into code every round in two governed projects. Authority and protected actions still bound every fix, and evidence directs attention without an exhaustive audit.

**Status.** `Contract`. Behavior `UNVERIFIED`.

**Reopens when.** A run shows speculative redesign, authority expansion, endless improvement, a missed supported risk, or a real break declined as a non-finding.

## Kernel and package shape

### One CTO kernel with optional workflows

The `skiphow` kernel governs every request about the current project. Six optional workflows add owner-chosen patterns: bug, plan, longrun, deploy-ready, fast-fixes, and simplify. Each links the kernel by relative path instead of copying it.

**Why.** The owner wants recurring work patterns under one CTO, and ordinary requests need none. A link is not enforced loading, and a linked file reaches context whole only when it fits one tool view.

**Status.** `Deterministic` for package shape, kernel links, and the one-view size of every runtime Markdown file. Workflow loading `UNVERIFIED`.

**Reopens when.** Runs show missed kernel loading, misselection, or contradictory contracts, a host offers a stronger dependency mechanism, or the view limit changes.

### Invariants in the kernel, method in playbooks

The always-loaded kernel holds authority, owner decisions, the engineering standard, custody, delegate obligations, direction when the result waits on the owner, and completion. Method lives in the playbook whose trigger names the act. The kernel's one point-of-use duty is to read `delegation` and set each delegate's route before dispatch.

**Why.** Correct behavior must not depend on opening an optional file, and small work should not inherit a fixed workflow. Claude Code cuts a failing command's output to about 10,000 characters, agents read skill files in chained commands that fail, and successful output shows far more, so the failing path binds. 545 of 569 recorded shell reads of the kernel were unnumbered, so [`check.py`](../scripts/check.py) caps raw characters at 9,900.

**Status.** `Deterministic` for the limit; a non-blocking lint flags a playbook within 500 characters of it. `Observed`: the dispatch duty opened `delegation` before the first dispatch where a topic list did not.

**Reopens when.** The kernel causes ceremony or misses a duty, a trigger is unrecognizable unopened, the failing-output cut changes, or numbered shell reads become common.

### Governed sessions reopen the kernel after compaction

A session the kernel or a workflow governed reopens the kernel, and that workflow, after compaction. A workflow loads the kernel by invoking the `skiphow` skill where the host has a skill tool.

**Why.** Codex keeps no package text across compaction, and only the skill description survives on both hosts. Three Claude sessions that read the kernel as a file lost it after compaction and never re-read it; three that invoked the skill had it re-attached each time.

**Status.** `Contract`. Effect `UNVERIFIED`.

**Reopens when.** A governed session still never reopens the kernel after compaction.

### Host-native execution first

SkipHow runs on each host's own execution and admits a thin binding only for a demonstrated gap.

**Why.** Duplicated runtime state adds cost, the workflows reuse one kernel with no service or custom workers, and a new component needs host schema, safety, and compatibility checks.

**Status.** `Deterministic` for the package shape. Adapter benefit needs receipts.

**Reopens when.** A controlled check shows a binding is needed to preserve an outcome.

### Default governance comes from one owned instruction block

Governance comes from one owned, reversible block in the trusted user instruction file the host actually reads, managed by [`activation.py`](../plugins/skiphow/skills/skiphow/scripts/activation.py) and the setup playbook. Explicit invocation is the fallback, and no hook ships.

**Why.** A block in a shadowed file configures nothing. Codex reads a non-empty `AGENTS.override.md` over `AGENTS.md` in `CODEX_HOME`, and Claude Code reads `CLAUDE.md` and unconditional `rules/` under `CLAUDE_CONFIG_DIR`, so the helper resolves the file the same way and reports configured, available, and loaded apart. An isolated Codex profile can log in, and an isolated Claude profile still cannot, which blocks a clean Claude activation receipt.

**Status.** `Deterministic` for the helper. `Observed` once each for Codex loading from both files. Claude loading `UNVERIFIED`. A comparison with a `SessionStart` hook and an `@import` is specified and not run.

**Reopens when.** A host changes discovery order, a receipt shows missed or false activation, or another mechanism passes the whole enable, disable, upgrade, and uninstall lifecycle.

## Engineering standard

### The kernel carries an engineering standard

Every request loads a standard that counts everything added as a permanent cost. It asks for the least that delivers the outcome, removal on the same terms as addition, causes fixed instead of hidden, no test-only production code, no layer before a second caller or real boundary, native tools first, and working files deleted when work lands, and it treats test or tooling growth past the product as a defect. A test names the break a user or caller would notice before anyone writes it, and every implementation and review brief pastes the section.

**Why.** Two governed projects grew test and tooling code past product code. Test guidance in references reached about one in twenty test-writing delegates, because delegates do not inherit skills and briefs did not carry it. Guards for money, security, customer data, and the release path still pay.

**Status.** `Contract`. Behavior `UNVERIFIED`.

**Reopens when.** Sessions still add pin tests, source-reading tests, custom selectors, or three or more review rounds on ordinary changes, or agents drop a guard for money, security, or data.

### Change the owner of a behavior and delete what it replaces

Simplification keeps the accepted behavior at the lowest total cost. A change extends the code that owns a behavior. A replacement moves every in-repository caller and deletes the old path, shims, and stale guidance, keeping compatibility only for outside consumers that exist now. Where one implementation must keep owning a behavior, the code makes that owner obvious, and the linter or type checker enforces it, never a test that reads source.

**Why.** Debt builds up one locally reasonable change at a time, and audits found it in kept shims, copied rules, and stale guidance. Advice to enforce ownership with failing checks such as import-rule tests produced source-reading tests in the field.

**Status.** `Contract`. Behavior `UNVERIFIED`.

**Reopens when.** A run keeps needless machinery, removes a form an outside consumer needs, or loses behavior a caller relied on.

### Inherited rules and tooling are the lead's to judge

Rules, tools, and records earlier sessions made are the lead's own decisions, even a technical option the owner picked from an agent's list. The lead revises them when they cost more than they protect, and only what the owner's own words require stays the owner's. Project instructions cover only what code and tooling cannot show, and never make agents add artifacts.

**Why.** Agent rules such as "every bug gets a regression test" drove the growth. Field agents kept an agent-chosen line limit and an agent-built test selector as owner decisions because the owner picked from a menu and commits carried the owner's account. Provenance is the owner's words in messages, issues, or history, and product choices stay the owner's even when picked from a list.

**Status.** `Contract`. Behavior `UNVERIFIED`.

**Reopens when.** A run rewrites a rule the owner set in their own words, or keeps an agent-made rule or tool whose cost it has measured.

### Fix the shared cause of a repeated failure

When a failure repeats, the lead fixes its shared cause and the other instances, with no guard per instance.

**Why.** Per-instance fixes sent the owner hunting the next one, and "fix the class" was read in the field as "add a guard for the class".

**Status.** `Contract`. Effect `UNVERIFIED`.

**Reopens when.** A run sweeps unrelated surfaces on a first report or adds one guard per instance.

### Design the journey and reuse maintained compositions

The agent uses available skills and tools when they pay, designs the affected journey in its product context, and reuses maintained compositions, not only primitives. Plans record those decisions apart from the capability that produced them.

**Why.** An implementation recreated part of an established composition despite a reuse requirement. An executing host may lack the planner's plugins, and a project with no design system still needs coherent shared pieces.

**Status.** `Contract`. Effect `UNVERIFIED`.

**Reopens when.** A run recreates a composition despite a reuse constraint, adds specialist ceremony to settled work, invents or installs capabilities, or asks the owner about routine interaction details.

## Workflows

### Simplify runs only on the owner's request

The simplify workflow measures the project, removes what does not pay through reviewed delivery, measures again, and revises the agent-made rules and tooling that caused the waste. It judges project tooling by cost per run and in fixes against what it catches and what native options offer, since the agents and jobs that run it are not the callers that justify it. It keeps guards for money, security, customer data, and the release path, and a cut that cites other coverage holds only after someone reads that coverage.

**Why.** An owner's hand cleanup went too far before the guards came back. Field runs kept an agent-built selector until the owner questioned it, and deleted tests on coverage nobody had opened. The shared frontmatter cannot disable implicit selection, so the description limits it to an owner request. Protected actions keep their grants.

**Status.** `Contract`, owner-requested. Behavior `UNVERIFIED`.

**Reopens when.** A run removes a protecting guard, offers the owner a technical menu, or activates on an ordinary change.

### Plan prepares the whole scope

The plan workflow prepares the whole requested scope, keeps the product interview open while answers are pending, and returns a short launch for the fitting workflow. Only the owner reduces scope, and an execution workflow the owner chose is kept.

**Why.** A recorded question is not finished preparation, and a ready task does not authorize a smaller scope. One outcome can hide uneven work, so the plan reviews actual one-agent workload. Host controls govern waiting. A mature path needs no foundation stage, and file, line, and acceptance counts set no universal limit.

**Status.** `Contract`. Behavioral improvement `UNVERIFIED`.

**Reopens when.** A run launches early, loses follow-up, takes assumptions as product choices, interviews endlessly or technically, fragments needlessly, omits safety, or expands authority.

### Plan tasks are dispatchable slices

Every task in a prepared plan has one verifiable outcome that one agent can carry from its record to a verified, reviewable change. The plan sizes every task now, and its independent review covers every task as published.

**Why.** Tasks that defer their own split leave a plan undispatchable, and a review of the specification alone lets them through. Ordinary delegation sizes only the next outcome, so the lead rechecks a later task at dispatch when an earlier result changes it.

**Status.** `Contract`. Behavioral improvement `UNVERIFIED`.

**Reopens when.** A plan still publishes a task with several outcomes or a deferred split, or the rule forces small cohesive work into needless tasks or speculative decomposition.

### Fast-fixes keeps live work moving, deploy-ready lands it

Fast-fixes coordinates a stream of local work across stacks, keeps every shown state recoverable, and continues independent work after showing a result. Deploy-ready reconciles active work into one checked candidate and carries it to the authorized destination.

**Why.** The owner asked for live orchestration. An earlier fast-fixes required a browser and a worktree, stopped after every shown result, and deferred every test run. The shared playbooks already cover delegation, tracking, and integration. Host controls decide concurrency and when messages arrive. Restrictions and protected-action grants survive upgrades.

**Status.** `Contract`, owner-requested. Nine corpus cases are not run.

**Reopens when.** A run loses incoming work, accepts stale returns, lets blocked work stop independent outcomes, misuses shared resources, loses checkpoints, adds needless infrastructure, or hides verification gaps.

## Delegation

### Delegates write only in verified isolation, at a chosen route

Delegates stay read-only unless the lead verifies writer isolation. The lead sets model and effort separately at the cheapest route likely to pass, keeps a route proven on comparable work, and counts an unset control as a choice because its default is often the parent's. Each brief carries the kernel path and bounds further delegation; the delegate is CTO of its brief, and the lead keeps owner questions, dispositions, and records.

**Why.** One checkout has one index and branch, and a delegate's report of its own isolation is not proof. Nested delegates often inherit the route, so the brief is where fan-out is bounded. A review's independence and framing matter more than its model level. No portable isolation or model-level interface exists, so unverifiable isolation takes the safe fallback.

**Status.** `Contract`. The motivating failures are `Observed`: five lanes writing one checkout, and a worktree that reported success into the shared tree.

**Reopens when.** A portable capability interface appears, a host makes isolation verifiable and default, or paired runs settle the routing cost question.

### Size assignments for the whole job

An assignment's size counts implementation, verification, and review. A long assignment names expected progress and when to return. Checkout isolation leaves the stash, services, databases, ports, and output paths shared.

**Why.** Independent repairs are not interface migrations, and useful progress can come before any commit. Existing evidence may be enough to size work, checkpoints follow project policy, and host waits and events let the lead observe without new state. A bare stash pop can take another lane's work.

**Status.** `Contract`. Effect `UNVERIFIED`.

**Reopens when.** A run splits needlessly, interrupts healthy work, misses progress breaches, or damages shared state.

### Handoffs stay compact and keep every finding

Bulky artifacts travel by reference. A correction carries current evidence and the findings and blockers still open. Every finding, blocker, and uncertainty survives the handoff. A return lists findings apart from its status, and the lead settles each one on acceptance. Shortened check output keeps the check's own exit status.

**Why.** In field sessions leads never mentioned again 51 of 124 items their delegates raised. A lead can read a return-size rule without passing it on, and a filter can succeed while the check fails.

**Status.** `Contract`. Four corpus cases are not run.

**Reopens when.** A run loses findings, accepts inaccessible proof, writes blanket report files, copies bulk into the coordinator, or takes a filter's status as the check's.

## Delivery and custody

### All project engineering state is the lead's

Every branch, worktree, checkout, checkpoint, running service, and uncommitted change in the project is the lead's, made by this session, an earlier one, or a delegate, and work is done only when verified at its authorized destination. A change request retires integrated, unheld leftovers, and the lead retires a superseded or abandoned attempt on its own judgment, naming its unique commits. Foreign uncommitted changes, live lanes, and anything under a read-only request stay untouched.

**Why.** The owner writes no code, so state reported as someone else's is false and hands a decision to the one person who cannot make it. Retiring recoverable state is engineering, not material deletion: Git recovers a deleted branch, and nothing recovers an uncommitted file. Liveness shows in moving changes, an open review, a live record, or a host-listed session, never in a name, a timestamp, or a running process alone.

**Status.** `Contract`. Custody corpus cases are not run.

**Reopens when.** A run retires a live lane, an uncommitted file, a still-defective attempt, or anything under a read-only request, small changes grow sweeps or custody ceremony, a human-coded project comes under SkipHow, or the owner asks for a retired branch or report-and-wait back.

### Reconcile project state before changing it

Reconciliation rebuilds state from live Git, reviews, destinations, and revision-specific checks before changing anything. Status reports dispositions, record correction changes only records, and change requests retire leftovers. Only an outcome-to-workspace link that cannot be rebuilt becomes durable.

**Why.** Tracker state, branch names, merge status, and CI can each be stale or point at the wrong revision. A parallel registry would be one more claim to reconcile, and workspace ownership cannot always be rebuilt after a session ends.

**Status.** `Contract`, with `Deterministic` corpus validation.

**Reopens when.** Live evidence cannot recover a material transition, the stored link proves insufficient, or the ordering adds ceremony without preventing a failure.

### Recover a failed merge by consequence

A disposable failed merge may stay for diagnosis. The lead contains or restores a shared target, and restoring production keeps its own grant.

**Why.** Leaving every failed merge in place made a broken shared branch the default. Containing a covered non-production destination is within the established workflow.

**Status.** `Contract`. Behavior `UNVERIFIED`.

**Reopens when.** A run restores a target it should have left, or leaves a shared target broken.

## Verification

### Verify the final state once and reuse the pass

Verification checks the final state at the interface callers use. Every role reuses a pass for the same command, tree, and environment, and reruns only on changed inputs, an unverifiable result, or a named doubt. Slow or flaky suites are measured and fixed at the layer that costs the time, with the runner's and CI provider's native features before custom tooling.

**Why.** Releases repeated equivalent gates, and wording that blessed building test selection preceded custom selectors and queues in both governed projects. A different tree still needs its own evidence, including revision-bound CI. Suite size and speed alone show neither the cause of slowness nor adequate coverage.

**Status.** `Contract`. One installed session that repeated equivalent gates motivated it. Behavior `UNVERIFIED`.

**Reopens when.** A run drops a protecting check, builds custom selection before the native one, or repeats an equivalent gate.

## Evaluation and evidence

### Receipts prove model behavior

Only receipts from real runs prove model behavior. Checks and CI never start a model, and a paid run is the owner's call.

**Why.** A green check proves no behavior, and receipt cost does not track what it settles: one pass spent $165 on a question four sessions under six dollars answered.

**Status.** Policy.

**Reopens when.** A host offers repository-preserving runs against an exact installed package with trustworthy receipts.

### Evaluation oracles name outcomes

Graders name outcomes, never implementations, and [`capture_eval.py`](../scripts/capture_eval.py) preflights each fixture against `evals/preflight.json` before model spend.

**Why.** An oracle once banned a binding the contract permits, and a prompt named a branch its fixture never created.

**Status.** `Deterministic`.

**Reopens when.** A scenario needs an outcome the registry or grader cannot express.

### Deterministic checks protect contracts only

Blocking checks cover package and host contracts, security and release invariants, and corpus semantics. Wording and presentation get a lint at most.

**Why.** A check that pinned a sentence or a topology froze editorial choices and protected nothing a host depends on.

**Status.** `Deterministic`.

**Reopens when.** A host starts depending on a detail now treated as editorial.

### Evidence labels belong to a claim

Suite status reports declared coverage with no behavioral label, and terminal coverage needs a verified fixture manifest and a retained end state. Each claim outside the suite has its own evidence rule: loaded, delivered at destination, foreign work preserved, completion honesty, or comparative benefit. A confirmed failure is `FAIL`, and a loading observation labels nothing else.

**Why.** One run cannot support eleven unrun scenarios or another host, and prose cannot replace inspectable state. The per-claim rules were fixed before any new run and validated against retained captures.

**Status.** `Deterministic` in [`claim_eligibility.py`](../scripts/claim_eligibility.py). Suite behavior `UNVERIFIED`.

**Reopens when.** A claim needs evidence no rule expresses, or a rule weakens what `Observed` means.

## Portability and privacy

### Runtime policy names no provider

The package carries no model IDs, cost tables, host tiers, dated host snapshots, or version-qualified host products.

**Why.** Host metadata changes faster than releases and can be checked at use time. Maintainer evidence keeps dated host versions.

**Status.** `Deterministic` for model IDs, scanned on every run.

**Reopens when.** A portable capability interface appears or a host version joins the public contract.

### Public receipts carry no private data

Public receipts exclude account and authentication metadata, known credential formats, private paths, raw host identifiers, and encoded home-derived directory names. Per-run usage, synthetic artifacts, and correlation through pseudonyms stay.

**Why.** Literal path replacement once left account metadata in a retained trace, and no filter can certify arbitrary prose.

**Status.** `Deterministic` in [`receipt_privacy.py`](../scripts/receipt_privacy.py).

**Reopens when.** A host adds a private field or a receipt needs stronger privacy review.
