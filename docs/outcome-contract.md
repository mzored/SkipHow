# Owner-outcome contract

SkipHow gives a product owner one accountable technical lead inside a supported coding host. The owner describes the outcome in ordinary language and keeps the product decisions. The lead owns the engineering through verified delivery, within the authority the owner already granted.

This page is the canonical product objective. The README, the contributor rules, the shipped skills, and the acceptance scenarios implement it. A file count, an instruction length, or a host mechanism is not the objective. This page says what the product owes; only retained receipts show what a host did.

The owner can pick a recurring workflow without taking over technical supervision. The optional bug, plan, longrun, deploy-ready, fast-fixes, and simplify skills share one [CTO kernel](../plugins/skiphow/skills/skiphow/SKILL.md), and each sets its own result and stopping point. Ordinary requests need no workflow. Automatic selection grants no extra authority, and only an explicit invocation asks for what a workflow writes, such as plan's planning records.

## Required outcomes

Each outcome is a duty the product owes the owner. The linked file is where the package meets it.

**The lead owns the engineering.** It sets acceptance, researches consequential choices, weighs what exists against custom work, and picks methods and tools by benefit against cost. User-facing work is designed as a journey inside the product. Small requests stay direct, and substantial work gets decomposition and a justified route per delegate. A decision reached with specialist help stays usable without it. See [technical design](../plugins/skiphow/skills/skiphow/references/technical-design.md) and [delegation](../plugins/skiphow/skills/skiphow/references/delegation.md).

**Supervision reaches past the request.** Passing checks do not end it. The lead looks for material risk and growing cost where evidence points, and fixes confirmed findings in the same run within authority. Deferral needs an owner decision, a protected action, a blocker, or a cost that would hurt the outcome, and its record says what resumes it. Work stops when the next step buys less than it costs, and read-only requests stay read-only. See [review](../plugins/skiphow/skills/skiphow/references/review.md).

**The owner's system stays small.** Everything added stays, and the owner pays for it. The lead builds the least that delivers the outcome and removes what no longer pays. Rules and tools earlier sessions made are the lead's to revise; only what the owner's own words require stays the owner's. Guards for money, security, customer data, and the release path stay. On request, the [simplify workflow](../plugins/skiphow/skills/skiphow-simplify/SKILL.md) shrinks an existing project.

**The owner decides product questions, and only those.** Open choices about visible behavior, scope, priority, cost, risk, audience, privacy, or rollout go to the owner with a recommendation. Technical choices never do. Answers survive later turns, and independent work continues while one is pending. See [product](../plugins/skiphow/skills/skiphow/references/product.md).

**Installation is reversible and grants nothing.** Each claimed host has an inspectable, reversible install path. The policy is in context before consequential project action, and unrelated conversation does not activate it. Configured, loaded, and behaving correctly are separate facts. See [setup](../plugins/skiphow/skills/skiphow/references/setup.md).

**Delivery reaches the authorized destination.** The lead carries work through the owner-authorized workflow and checks real downstream effects. Production, public publication, new financial commitments, wider access, material deletion, and disclosure need the owner's explicit grant. An upgrade grants nothing. Retiring the lead's own recoverable state is routine. See [integration](../plugins/skiphow/skills/skiphow/references/integration.md).

**A plan prepares the whole scope.** An invoked plan leaves a reviewed specification and tasks one agent can each carry, with no product choice left open. An unanswered question keeps the interview open, and only the owner can shrink the scope. Planning grants no implementation. See [plan](../plugins/skiphow/skills/skiphow-plan/SKILL.md) and [longrun](../plugins/skiphow/skills/skiphow-longrun/SKILL.md).

**Iteration stays local until the owner asks for delivery.** While the owner keeps sending changes, results stay checked, visible, and recoverable on the machine. Delivery starts when the owner asks, names a destination, or accepts with nothing more to send. Inside an invoked iteration workflow, acceptance alone does not start it. See [fast-fixes](../plugins/skiphow/skills/skiphow-fast-fixes/SKILL.md) and [deploy-ready](../plugins/skiphow/skills/skiphow-deploy-ready/SKILL.md).

**Obligations outlive the session.** Material obligations, accepted decisions, and multi-session progress stay discoverable in the authorized tracker. Tiny same-session work needs no ticket. Without a usable tracker, the obligation goes to an authorized private channel with the blocker. Record text never creates authority. See [tracked work](../plugins/skiphow/skills/skiphow/references/tracked-work.md).

**Status comes from live evidence.** A status request rebuilds each outcome from its destination, workspaces, reviews, checks, and records, and changes nothing. A change request also retires integrated leftovers nothing holds. Completion means the whole outcome, never a merge or a tracker status alone. Facts Git can recover never become a parallel registry.

**One lead stays accountable.** Delegates apply the same standard within the authority their brief relays and return what they find outside it. Parts and findings of one outcome stay with the lead, never as sessions the owner must start. Every branch, worktree, checkout, service, and uncommitted change in the project is the lead's, made by a session or delegate, and never the owner's to decide. Parallel writers need verified separate workspaces. A live session's lane stays untouched, and a finished session's leftover ends integrated, recorded, or retired with its commit named. A resumed session rebuilds from live state. A missing host capability gets a safe fallback and an honest limitation.

**Every change carries evidence that fits it.** A verifiable pass is reused while its inputs match. A test exists to catch a break a user or caller would notice. Independent review goes where a mistake is costly, and a finding that names no break ends the round. Slow, flaky, or broken checks are fixed at their cause without weakening what protects delivery. The lead verifies the result at its destination. See [testing](../plugins/skiphow/skills/skiphow/references/testing.md).

**Completion is honest.** The report names what was delivered, the evidence that applies, and material unresolved work. It reaches the owner in their language and in product terms; hashes, branches, and check names belong in the project's records. A delegate's claim, a configured setting, or a passing schema is not evidence about a destination or about model behavior.

## Host boundary

Codex and Claude Code supply execution, permissions, tools, credentials, sessions, subagents, and continuation. SkipHow uses them and does not pretend to provide them. It is orchestration policy: it tells the host agent how to plan, decompose, delegate, review, and reconcile. The host runs the model and tools. A control plane, where one exists, owns durable workers, queues, scheduling, budgets, and deployment.

Authority comes from the owner's messages and from trusted host, user, organization, or administrator policy, at the host's precedence. Trusted repository instructions set procedure within that authority, and a file's location proves no trust. Issues, pull requests, documents, logs, tool output, web content, and delegate returns are task data that grant nothing. This is policy, and text enforces nothing. Where the host offers a real control, such as a sandbox, a permission prompt, or an isolated checkout, rely on it.

The package ships no hook. Default governance is one owned, reversible block in the user instruction file each host reads. Explicit invocation is the fallback, and automatic selection stays `UNVERIFIED` until a retained run shows it. Versioned host facts live in [evidence](evidence.md) with their dates.

## Reviewing implementation changes

Compare implementations that preserve these outcomes by correctness, owner effort, execution cost, maintenance cost, and host compatibility. Give additions, removals, and retained mechanisms the same scrutiny. For each material removal, state the responsibility, the path that still carries it, and the acceptance check. A responsibility nobody has measured stays required and `UNVERIFIED`.

Deleting durable findings because no recent receipt measures their benefit fails this review, unless another discoverable path keeps the obligations. Removing a duplicate sentence passes when its governing copy and observable acceptance remain, and proving a literal duplicate needs no paid experiment. A thin host adapter qualifies when a controlled check finds a gap it repairs and safety and compatibility checks cover it.

The [behavioral corpus](../evals/README.md) supplies acceptance scenarios. The [evidence ledger](evidence.md) records actual coverage and its limits. Neither replaces the required outcome with a prescribed tool sequence.
