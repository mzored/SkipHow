# Current decisions

SkipHow's live decisions under the [owner-outcome contract](outcome-contract.md). The shipped files state each rule, and each entry links the one that carries it. This page keeps what those files cannot show: the observation behind the rule and what would reopen it.

How to read an entry:

- An entry with no status line is `Contract` with behavior `UNVERIFIED`. The shipped text encodes it, and no retained run has tested that text. `Deterministic` means a check proves it on every run. `Observed` means a retained run showed it, and [evidence](evidence.md) holds the receipt.
- Every decision reopens when a run shows its rule broken, or costing more than the failure it prevents. An entry lists only its other triggers.
- Earlier text is context to weigh, never a veto. The [page as of 7.0.8](https://github.com/mzored/SkipHow/blob/90cfdbbbf2a354973ede4d716853ce62886e2c6b/docs/decisions.md) states all 33 earlier entries at full length, with each one's list of failure signs. The [table as of 7.0.1](https://github.com/mzored/SkipHow/blob/2f72c7f218f29db20421eddce6d280e0d6f52045/docs/decisions.md) keeps each row's version history, and the [older narratives](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/decisions.md) keep the rest.

## Authority and the owner

### Authority comes from the owner, and a grant sets what travels

Rule in [kernel, Authority](../plugins/skiphow/skills/skiphow/SKILL.md#authority).

**Why.** Anyone can plant a file in a repository, and hosts load instruction files at their own precedence, so location proves no trust. A record the owner points at authorizes its outcome and nothing more. Invoking the plan workflow requests records, and automatic selection grants nothing. Preparation and production are separate grants, and local combination grants no publication. The workflow settles what may travel, not how often, so the lead batches accepted results.

**Reopens when.** A host ships enforced provenance.

### The owner decides product questions and reads product reports

Rule in [kernel, Decisions](../plugins/skiphow/skills/skiphow/SKILL.md#decisions) and [Done](../plugins/skiphow/skills/skiphow/SKILL.md#done).

**Why.** Keeping the owner out of engineering is the boundary this product exists to hold. An owner who writes no code reads reports to decide what to look at next. Accounting they cannot use costs them attention every turn, and a later agent or reviewer needs it in the project's records. Several checkouts of one project answer on the same default address, so a shown result names its branch and address. A one-off workaround for a standing host refusal comes back on every run that meets it, so the owner gets one request for a lasting permission.

**Reopens when.** An owner asks for the technical options or detail they no longer see.

### The lead fixes confirmed findings across the project and keeps every part

Rule in [kernel, Engineering standard](../plugins/skiphow/skills/skiphow/SKILL.md#engineering-standard), [Custody and delegates](../plugins/skiphow/skills/skiphow/SKILL.md#custody-and-delegates), and [review](../plugins/skiphow/skills/skiphow/references/review.md#receiving-findings).

**Why.** A narrow pass can leave material risk or recurring cost elsewhere. An earlier rule to resolve every feasible finding, with no bar on what counted, turned reviewer requests for more tests and guards into code every round in two governed projects. Field sessions left confirmed findings listed but unfixed, filed, or carded for the owner because they lay outside the request, and one went unrepaired for a month. A session the owner has to start makes the owner the coordinator this product exists to replace, and its result never returns to the lead.

**Reopens when.** A delegate fan-out costs more than the owner-started session it replaced, or a host makes owner-visible sessions report back to the lead.

## Kernel and package shape

### One kernel holds every invariant, and workflows and playbooks hold method

The `skiphow` kernel governs every request about the current project and fits one host tool view. Six optional workflows link it by relative path: bug, plan, longrun, deploy-ready, fast-fixes, and simplify. Method lives in the playbook whose trigger names the act. The kernel's one point-of-use duty is to read `delegation` and set each delegate's route before dispatch.

**Why.** Correct behavior must not depend on opening an optional file. A topic list gets a playbook opened less reliably than an obligation phrased against the act. A link is not enforced loading, and a file reaches context whole only when it fits one tool view. Claude Code cuts a failing command's output to about 10,000 characters, and agents read skill files in chained commands that fail. Successful output shows far more, so the failing path binds. The Read tool showed a 36.7 KB file whole. 545 of 569 recorded shell reads of the kernel were unnumbered, so [`check.py`](../scripts/check.py) caps raw characters at 9,900, leaving room for a short error line.

**Status.** `Deterministic` for package shape, kernel links, and the size limit. A non-blocking lint flags a playbook within 500 characters of it. `Observed`: the dispatch duty opened `delegation` before the first dispatch where a topic list did not. Workflow loading `UNVERIFIED`.

**Reopens when.** A host offers a stronger dependency mechanism, the failing-output cut changes, or numbered shell reads become common.

### Governed sessions reopen the kernel after compaction

Rule in each workflow's opening paragraph, for example [bug](../plugins/skiphow/skills/skiphow-bug/SKILL.md), and in [kernel, References](../plugins/skiphow/skills/skiphow/SKILL.md#references).

**Why.** Codex keeps no package text across compaction, and only the skill description survives on both hosts. Three Claude sessions that read the kernel as a file lost it after compaction and never re-read it. Three that invoked the skill had it re-attached each time.

### Host-native execution, and one owned instruction block

SkipHow ships no hook, service, or custom worker. Default governance is one owned, reversible block in the trusted user instruction file the host reads, managed by [`activation.py`](../plugins/skiphow/skills/skiphow/scripts/activation.py) and the [setup playbook](../plugins/skiphow/skills/skiphow/references/setup.md). Explicit invocation is the fallback.

**Why.** Duplicated runtime state adds cost, and a new component needs host schema, safety, and compatibility checks. Host documentation establishes instruction loading, not correct selection, and a block in a shadowed or unread file configures nothing. Codex reads a non-empty `AGENTS.override.md` over `AGENTS.md` in `CODEX_HOME`, and Claude Code reads `CLAUDE.md` and unconditional `rules/` under `CLAUDE_CONFIG_DIR`. The helper resolves the file the same way and reports configured, available, and loaded apart.

**Status.** `Deterministic` for the package shape and the helper. `Observed` once each for Codex loading from `AGENTS.md` and from `AGENTS.override.md`. Claude loading `UNVERIFIED`, because an isolated Claude profile cannot log in. A comparison with a `SessionStart` hook and an `@import` is specified and not run.

**Reopens when.** A host changes discovery order, a controlled check shows a binding is needed to preserve an outcome, or another mechanism passes the whole enable, disable, upgrade, and uninstall lifecycle.

## Engineering standard

### The kernel carries an engineering standard

Rule in [kernel, Engineering standard](../plugins/skiphow/skills/skiphow/SKILL.md#engineering-standard). Every implementation and review brief pastes it.

**Why.** Two governed projects grew test and tooling code past product code, built custom selectors and gates, and kept shims and copied rules. The earlier package text made each addition a gain and each removal a risk. Test and design guidance in references reached about one in twenty test-writing delegates, because delegates do not inherit skills and briefs did not carry it. Advice to enforce ownership with failing checks, such as import-rule or exhaustiveness tests, produced source-reading tests in the field, so the linter or type checker enforces it.

**Reopens when.** Sessions still add pin tests, source-reading tests, custom selectors, or three or more review rounds on ordinary changes, or a run drops a guard for money, security, or data.

### Inherited rules and tooling are the lead's to judge

Rule in [kernel, Authority](../plugins/skiphow/skills/skiphow/SKILL.md#authority). Only what the owner's own words require stays the owner's.

**Why.** Agent rules such as "a recurring problem becomes a test", "every bug gets a regression test", and a coverage floor drove much of the growth, and the earlier package treated every repository instruction as owner procedure. Field agents trimmed code to fit an agent-chosen line limit, patched an agent-built test selector, and kept both as owner decisions because the owner picked from a menu and commits carried the owner's account. Provenance is the owner's words in messages, issues, or history, never commit authorship or an answer to an agent's technical menu.

### Fix every place that shares the cause or role

Rule in [kernel, Engineering standard](../plugins/skiphow/skills/skiphow/SKILL.md#engineering-standard).

**Why.** Per-instance fixes sent the owner hunting the next one. "Fix the class" was read in the field as "add a guard for the class", so the rule names the cause as the fix. A rule that spoke only of repeated failures left an owner's design correction to the one element they pointed at, and a shared piece changed for one screen broke others nobody looked at.

### Design the journey and reuse maintained compositions

Rule in [product](../plugins/skiphow/skills/skiphow/references/product.md#designing-the-interaction) and [technical design](../plugins/skiphow/skills/skiphow/references/technical-design.md#reuse-before-custom-code).

**Why.** A planner loaded specialist guidance and required reuse, and the implementation still recreated part of an established composition. The package had described asking a product question, not designing the journey. Hosts list capabilities differently and an executing host may lack the planner's plugins, so plans record design decisions apart from the capability that produced them.

## Workflows

### Simplify runs only on the owner's request

Rule in the [simplify workflow](../plugins/skiphow/skills/skiphow-simplify/SKILL.md).

**Why.** An owner's hand cleanup went too far before the guards came back. Field runs kept an agent-built selector until the owner questioned it, because the agents and jobs that run a tool are not the callers that justify it. Reviews found real holes in test deletions justified by coverage nobody had opened. The shared frontmatter cannot disable implicit selection, so the description limits it to an owner request.

### Plan prepares the whole scope as dispatchable tasks

Rule in the [plan workflow](../plugins/skiphow/skills/skiphow-plan/SKILL.md).

**Why.** A recorded question is not finished preparation, and a ready task does not authorize a smaller scope. Tasks that defer their own split leave a plan undispatchable, and a review of the specification alone lets them through. The owner selects this workflow for a dispatchable task set, so it sizes the whole accepted scope where ordinary delegation sizes only the next outcome. An access, credential, or human step that only execution needs stays a blocker on its task and does not withhold the launch. The launch restates no grant, because a pasted launch is an owner message.

### Fast-fixes keeps live work moving, deploy-ready lands it

Rule in [fast-fixes](../plugins/skiphow/skills/skiphow-fast-fixes/SKILL.md) and [deploy-ready](../plugins/skiphow/skills/skiphow-deploy-ready/SKILL.md).

**Why.** The owner asked for live orchestration. An earlier fast-fixes required a browser and a worktree, stopped after every shown result, and deferred every test run.

## Delegation

### Delegates write only in verified isolation, at a chosen route

Rule in [kernel, Custody and delegates](../plugins/skiphow/skills/skiphow/SKILL.md#custody-and-delegates) and [delegation](../plugins/skiphow/skills/skiphow/references/delegation.md).

**Why.** One checkout has one index and branch, and a delegate's report of its own isolation is not proof. A delegate may not have this guidance in context, and nested delegates often inherit the route, so the brief is where fan-out is bounded. An unset control's default is often the parent's. No portable isolation or model-level interface exists, so unverifiable isolation takes the safe fallback.

**Status.** `Contract`. The motivating failures are `Observed`: five lanes writing one checkout, and a worktree that reported success into the shared tree.

**Reopens when.** A portable capability interface appears, a host makes isolation verifiable and default, or paired runs settle the routing cost question.

### Assignments are sized whole, and handoffs keep every finding

Rule in [delegation, The size of a unit](../plugins/skiphow/skills/skiphow/references/delegation.md#the-size-of-a-unit) and [What comes back](../plugins/skiphow/skills/skiphow/references/delegation.md#what-comes-back).

**Why.** In field sessions leads never mentioned again 51 of 124 items their delegates raised. A lead can read a return-size rule without passing it on, and a filter can succeed while the check fails. Checkout isolation leaves the stash, services, databases, ports, and output paths shared. A shared latest pointer can identify another lane's work, and a bare stash pop can take it.

## Delivery and verification

### All project engineering state is the lead's

Rule in [kernel, Custody and delegates](../plugins/skiphow/skills/skiphow/SKILL.md#custody-and-delegates), [integration, verifying the integrated state](../plugins/skiphow/skills/skiphow/references/integration.md#verifying-the-integrated-state), and [clearing away what the work created](../plugins/skiphow/skills/skiphow/references/integration.md#clearing-away-what-the-work-created).

**Why.** The owner writes no code and no third party does, so state reported as someone else's is false and hands a decision to the one person who cannot make it. Git recovers a deleted branch, and nothing recovers an uncommitted file, so retiring recoverable state is engineering and not material deletion. Liveness shows in moving changes, an open review, a live record, or a host-listed session, never in a name, a timestamp, or a running process alone. Dev servers, log streams, booted simulators, and test containers outlived the agents that started them for hours to days. Leaving every failed merge in place made a broken shared branch the default while diagnosis ran.

**Reopens when.** A human-coded project comes under SkipHow, the owner asks for a retired branch or report-and-wait back, or an owner loses a running preview they needed.

### Reconcile project state before changing it

Rule in [tracked work](../plugins/skiphow/skills/skiphow/references/tracked-work.md#reconciling-project-state).

**Why.** Tracker state, branch names, merge status, and CI can each be stale or point at the wrong outcome, revision, or destination. A parallel registry would be one more claim to reconcile. Live Git, reviews, destinations, and revision-specific checks establish every transition in the current cases, so only an outcome-to-workspace link that cannot be rebuilt becomes durable.

**Status.** `Contract`, with `Deterministic` corpus validation.

**Reopens when.** Live evidence cannot recover a material transition, or the stored link proves insufficient for safe recovery.

### Verify the final state once and reuse the pass

Rule in [testing](../plugins/skiphow/skills/skiphow/references/testing.md#reusing-a-verification-record).

**Why.** Releases repeated equivalent gates, and one installed session did the same. Wording that blessed building test selection preceded custom selectors and queues in both governed projects. Suite size and speed alone show neither the cause of slowness nor adequate coverage.

## Evaluation and evidence

### Receipts prove model behavior, and checks protect contracts only

Rule in [`AGENTS.md`](../AGENTS.md#evidence).

**Why.** A green check proves no behavior, and receipt cost does not track what it settles. One pass spent $165 on a question four sessions under six dollars answered. A check that pinned a sentence or a topology froze editorial choices and protected nothing a host depends on.

**Status.** Policy, with `Deterministic` checks.

**Reopens when.** A host offers repository-preserving runs against an exact installed package with trustworthy receipts, or a host starts depending on a detail now treated as editorial.

### Oracles name outcomes, and labels belong to a claim

Rule in [evidence](evidence.md#what-an-observed-claim-must-retain). [`capture_eval.py`](../scripts/capture_eval.py) preflights each fixture against `evals/preflight.json` before model spend.

**Why.** An oracle once banned a binding the contract permits, and a prompt named a branch its fixture never created. One run cannot support eleven unrun scenarios or imply another host, activation arm, or trial. A per-run standard left every earlier observation unlabelled while the ledger quoted them. The per-claim rules were fixed before any new run and validated against retained captures.

**Status.** `Deterministic` in [`claim_eligibility.py`](../scripts/claim_eligibility.py) and the corpus tests. Suite behavior `UNVERIFIED`.

**Reopens when.** A scenario needs an outcome the registry or grader cannot express, a claim needs evidence no rule expresses, or a rule weakens what `Observed` means.

## Portability and privacy

### Runtime policy names no provider, and public receipts carry no private data

Rule in [the contributor rules](../AGENTS.md#portability-and-safety). The package carries no model IDs, cost tables, host tiers, dated host snapshots, or version-qualified host products. Public receipts exclude account quota and authentication metadata, known credential formats, private paths, raw host identifiers, and encoded home-derived directory names.

**Why.** Both hosts change model names and controls independently and faster than releases, and host metadata can be checked at use time. Literal path replacement once left account metadata in a retained trace, and no filter can certify arbitrary prose.

**Status.** `Deterministic`: model IDs are scanned on every run, and [`receipt_privacy.py`](../scripts/receipt_privacy.py) checks receipts.

**Reopens when.** A portable capability interface appears, a host version joins the public contract, a host adds a private field, or a receipt needs stronger privacy review.
