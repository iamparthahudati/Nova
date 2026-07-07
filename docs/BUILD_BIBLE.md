# Nova — The Build Bible

**Status:** Cultural canon. Read this before your first commit; re-read when you are tired.  
**Audience:** Every engineer who touches Nova — human or AI — now and in 2036.  
**What this is:** The *why* behind how we build. The habits of mind, the product
convictions, and the judgment calls that should feel obvious after you've been here
a month.  
**What this is not:** Architecture (see `docs/adr/`, frozen specs), implementation
rules (see `NOVA_ENGINEERING_HANDBOOK_v1.md`), or a task list (see
`NOVA_IMPLEMENTATION_ROADMAP_v1.md`). Those documents tell you *what* is allowed.
This one tells you *how to think* while building inside it.

**Authority:** When this document and a frozen spec disagree about a boundary, the
spec wins. When this document and the Handbook disagree about a lint rule, the
Handbook wins. When you are unsure whether something belongs in Nova at all, this
document is the tiebreaker.

---

## I. The one thing we are building

Nova is not a collection of features. It is **a personal operating system that earns
the right to tell you what to do next** — across money, work, and life — by being
more honest than your memory and more disciplined than your spreadsheet.

The user is a founder (often solo) running a portfolio: products, clients, goals,
and a finite number of hours. Nova's job is not to give them more tabs, boards, or
metrics. Its job is to **reduce the number of decisions they have to make alone**
while **never making a decision for them they did not approve**.

If you remember nothing else:

> **Ground truth in ledgers. Meaning in derivation. Trust in explanation.**

Everything else in this document is commentary on that sentence.

---

## II. Product philosophy — what we owe the user

### 2.1 Decision support, not data entry

Every productivity tool ever built asked the user to be a **librarian first and a
doer second**. Nova deletes the librarian. The user's verbs are **capture,
decide, do** — not create-project, pick-folder, drag-card, update-status.

When you build a screen, ask: *Does this make the user maintain something, or does
it give them a decision they can act on in thirty seconds?* Maintenance is a tax.
Decisions are the product.

### 2.2 Every surface drives a decision

Not a board to admire. Not a metric to watch. A **decision to make**:

- What do I do now?
- What is slipping?
- What should I stop?
- Where should the next hour go?
- Is the portfolio moving forward?

If you cannot name the decision a feature improves, it does not ship. This is not
minimalism for aesthetics. It is **subtraction as strategy** — the same reason
Finance has four questions, not forty dashboards.

### 2.3 Calm, certainty, momentum

The product should feel like a chief of staff who has already done the reading:

- **Calm** — no badge anxiety, no infinite backlog guilt, no notification spam.
- **Certainty** — one defensible answer to "what matters," with reasons one tap away.
- **Momentum** — the system moves work forward even when the user does not touch it
  (capture lands in the right place; plans adapt; nothing lives only in their head).

If your PR adds visual noise, optional complexity, or "just in case" configuration,
you are working against the product.

### 2.4 The AI is a chief of staff, not a task manager

Nova proposes. The human commits. The AI explains. The AI says "I'm not sure" when
it is not sure. The AI tells the user to **do less** when that is the honest answer
— even though an engagement-optimized product never would.

**Aligned to outcomes, not engagement.** We do not optimize for time-in-app,
streak-guilt, or notification opens. We optimize for **better allocation of attention
over years**.

### 2.5 Graceful degradation is a feature, not a fallback

With Brain offline, Nova must still be **excellent software** — a fast, local,
trustworthy instrument. AI makes Nova a chief of staff; its absence makes Nova a
precision tool, not a broken demo.

Never ship a flow where the critical path requires a model.

### 2.6 Local-first is a promise, not an implementation detail

The user's finances, work, conversations, and eventually their screen context are
the most private data they own. **The device is the vault.** Cloud is for reasoning
when necessary — not for storage, sync, or surveillance.

Building "just this once" against local-first to move faster is borrowing against
ten years of trust.

---

## III. Engineering philosophy — how we think in code

### 3.1 We build instruments, not applications

Finance is not an accounting app — it is a **money instrument**: a small ledger and
ruthless derivation. WorkOS is not a project manager — it is an **attention
instrument**: two ledgers (commitment and time) and ruthless derivation.

When you add a field, ask: *Is this ground truth, or am I storing something I should
compute?* Storing derived state feels fast for a week and costs a year.

### 3.2 Boring code is a love letter to the future engineer

Cleverness that saves you ten minutes today and costs someone an hour at 2 a.m. in
2031 is a net loss. The obvious loop beats the elegant one-liner. The explicit
parameter beats the hidden global. The named intermediate variable beats the chain.

We are not impressing anyone. We are **being found** — by our future selves, by new
teammates, by agents reading the repo cold.

### 3.3 Decide, then do — always

Nova separates **pure decision** from **effect**:

- Build the mutation. Then finalize it.
- Compute the plan. Then persist it.
- Assemble the context. Then call Brain.

A function that both thinks and writes in one body will lie to you in tests and in
production. Split it.

### 3.4 Boundaries are not bureaucracy — they are cognitive load limits

`domains/work` does not import Finance because **coupling is cognitive debt**.
The facade exists so cross-domain truth is assembled in one visible place, not
smuggled through imports.

When you feel the urge to "just import it," you have found a seam that belongs in
the composition root or the API layer. That urge is useful; obey the architecture
instead of the shortcut.

### 3.5 Events are our memory of what happened

Every write is a `MutationEvent`. Not because we love ceremony — because **"what did
Nova do, and why?"** must be answerable in ten years without replaying guesswork.

If it changed state and did not produce an event, it did not happen in a way we
can trust or debug.

### 3.6 One source of truth, zero reconciliation

Two systems that both "know" the same fact will disagree. Nova chooses **one owner**
per fact:

- Cash → Finance
- Time spent → Time ledger
- Intent → Commitment ledger
- Document bodies → Knowledge

Everyone else holds pointers, expectations, or derived views. **Reconciliation is
computation, not storage.**

### 3.7 Personal scale, decade scale

Nova is not built for billions of rows or multi-tenant hypergrowth in v1. It is
built for **one person's data over ten years** — still fast, still intelligible,
still recoverable from a SQLite file on a laptop.

That constraint is liberating: we optimize for clarity and correct derivation, not
premature distributed systems heroics.

---

## IV. The Finance discipline (apply it everywhere)

Finance taught Nova how to build domains that survive. Treat these as cultural
instincts, not Finance-only rules:

| Instinct | Meaning |
|---|---|
| **Ledger, not balance** | Store movements and commitments; compute totals on read. |
| **Derived, never stored** | Priority, health, ROI, momentum — if the user didn't type it, we don't persist it. |
| **Integer truth** | Money in minor units; time in minutes; no floats where sums must be exact. |
| **Immutable history** | Closed time entries and financial facts don't get edited — they get adjusted forward. |
| **Explain the number** | Every score carries reasons; every forecast carries confidence. |
| **Propose, never silently mutate** | AI output is a proposal until the human commits. |

When WorkOS (or the next domain) tempts you to add a `health_status` column —
you are about to build the bug Finance was designed to avoid. Stop.

---

## V. Decision-making framework

Use this order when you face any non-trivial choice:

### Step 1 — Name the user decision

*"What decision does this improve?"* If the answer is blank, stop.

### Step 2 — Name the ground truth

What ledger row or aggregate does this create or change? If it doesn't touch ground
truth, it is probably a projection — keep it out of the database.

### Step 3 — Check the ten-year test

*"Will an engineer in 2036 understand why this exists without asking anyone?"*
If it requires oral tradition, write an ADR or don't build it.

### Step 4 — Check the subtraction test

*"What does this replace or refuse to build?"* Nova grows by **refusing** the
feature-graph of Jira × Notion × QuickBooks × Todoist. Addition without subtraction
is how products drown.

### Step 5 — Check the boundary test

*"Does this import sideways?"* Domain → domain, service → service (undocumented),
Brain outside Brain, sqlite outside Memory — any yes means pause.

### Step 6 — Check the trust test

*"Would I trust this with my own bank statements and my own calendar?"* Privacy,
local-first, explainability, and no silent writes are non-negotiable.

### When to escalate to an ADR

Stop coding and draft an ADR when you need to:

- Move a package boundary
- Add a dependency edge
- Change `MutationEvent`'s shape
- Store something derived "for performance"
- Make an external system authoritative
- Introduce a pattern the Handbook forbids

ADRs are not permission slips for redesign. They are **permanent records of
irreversible choices** so nobody "cleans up" load-bearing structure by accident.

---

## VI. Simplicity rules

These are defaults, not suggestions:

1. **One primary action per screen.** If you can't name it in one verb, the screen
   is doing too much.
2. **One write unit per user action.** One aggregate per mutation unless a
   sanctioned orchestration (documented, one transaction, one composite event).
3. **One Claude client.** Brain reasons; everything else prepares inputs.
4. **One persistence owner.** Memory writes SQLite; nowhere else opens it.
5. **One priority queue across life.** Work, clients, and goals compete for the
   same hours — the product must never hide that tradeoff in silos.
6. **One money type, one time type.** Shared conventions across domains; no second
   `Money` struct because importing felt hard.
7. **One way to wire dependencies.** The composition root. Not "just this once" in
   a router.
8. **Fewer concepts beat fewer lines.** Delete the abstraction that exists only to
   exist. Keep the abstraction that prevents a class of bugs forever.

**The simplicity question:** *Can this be removed without lying to the user?* If yes,
remove it.

---

## VII. Naming philosophy

Names are the cheapest documentation and the most-read code. We name like people
who expect strangers to maintain our work.

### Speak in domain language

Use the user's words in product-facing concepts: **commitment**, **holding**,
**brief**, **ledger** — not `EntityManager.process()`.

### Verbs tell the truth about side effects

| Prefix | Promise |
|---|---|
| `get_`, `list_` | Read only. Never writes. |
| `build_`, `compute_`, `assemble_` | Pure. No I/O. Same inputs → same outputs. |
| `create_`, `add_`, `log_`, `save_` | Persists. Lives at the effect edge. |
| `complete_`, `archive_`, `transition_` | Domain lifecycle change. Emits an event. |

A misnamed function is a lie. Callers will trust it and bugs will compound.

### Names encode time

Domain dates (`occurred_on`, `due_on`) are not audit timestamps. Mixing them is
how finance and work data get bucketed wrong **forever**. Name and type them so
the distinction is impossible to miss.

### Booleans are questions

`is_blocked`, `has_uncommitted_plan`, `should_surface_risk` — readable in an `if`
without a comment.

### Files name their single responsibility

If you cannot describe a file in one sentence, split it. The Handbook's size limits
are not pedantry — they are **forced focus**.

---

## VIII. Code quality as culture

The Handbook defines enforceable standards. This section defines the **spirit**
behind them:

### Correctness before cleverness

Exact sums, acyclic graphs, conflict detection, parameterized SQL — these are
moral obligations in a system that tells a founder where their money and hours went.

### Tests that prove reality

We test against real SQLite, not mocked databases. Mocks lie; founders' data doesn't.

Architecture tests are not CI vanity — they are **the immune system** against the
slow death of import spaghetti.

### Small diffs, sharp intent

A PR should do one thing understandable from its title. Drive-by refactors,
opportunistic renames, and "while I'm here" scope expansion erode review quality
and release confidence.

### Comments explain *why*, not *what*

The code says what. Comments exist for non-obvious business rules, invariant
rationale, and traps for the unwary — not for narrating obvious loops.

### Debt is visible

If you must defer, mark it: `DEBT(nova-xxx)` with a one-line reason. Hidden debt
is not debt — it is a landmine.

---

## IX. Anti-patterns — what we do not do here

These are not "sometimes okay." They are how Nova dies slowly:

| Anti-pattern | Why it kills us |
|---|---|
| **Stored derived state** ("we'll sync it on write") | Rot, divergence, untrustworthy dashboards — the Jira disease. |
| **Hand-maintained status** | User stops updating; product lies; 30-second test fails. |
| **Domain importing domain** | Coupling that makes every feature a negotiation. |
| **Brain in the domain layer** | Non-determinism everywhere; untestable core; key sprawl. |
| **Direct sqlite/lancedb outside Memory** | Second write paths; schema drift; backup nightmares. |
| **Silent catch / `except: pass`** | Failures become ghosts; personal finance and work data corrupt quietly. |
| **Float money or float time totals** | Pennies and minutes drift; ROI becomes fiction. |
| **Feature without a decision** | Metric museums; user ignores Nova; reverts to head + spreadsheet. |
| **Notification engagement hacks** | Breaks calm; destroys chief-of-staff trust. |
| **Autonomous mutation "for convenience"** | One scandal kills ten years of trust. Propose → commit. |
| **External system as source of truth** | GitHub/Jira/Calendar enrich; SQLite decides. |
| **Premature abstraction** | `AbstractAbstractFactory` today; nobody knows where logic lives tomorrow. |
| **Config surface for internal indecision** | We decide; users decide outcomes — not our architectural uncertainty. |
| **Copy-paste domain** | Second `Money` type, second habits table, second notification system — reconciliation hell. |

When you recognize one in review, name it plainly. No shame — we all feel the
shortcut. The culture is **catching it before merge**.

---

## X. AI usage guidelines (for humans and agents)

AI is how Nova thinks out loud. It is not a bypass around discipline.

### For human engineers

- Use AI to **explore and draft**, not to **merge what you don't understand**.
- You own the diff. "The model wrote it" is not a review.
- Point agents at `CLAUDE.md`, the Handbook, and this document before large tasks.
- If an agent proposes a boundary change, **stop** — that is your job and maybe an ADR.

### For AI coding agents

- **Read before write.** Match surrounding conventions exactly.
- **Minimize scope.** The smallest correct diff beats a refactor.
- **Never "fix" documented architecture deviations** without explicit human approval.
- **Never store derived values** because the prompt said "save the score."
- **Never add cross-package imports** not in `ALLOWED_EDGES`.
- **Propose schema changes; do not merge them** — database shape is human-gated.
- When uncertain, **stop and say so** — mirroring ADR 0016 inside the build process.

### Where AI belongs in the product

| AI does | AI does not |
|---|---|
| Structure captures from natural language | Silently create commitments |
| Propose plans, ranks, narratives | Persist proposals as truth |
| Explain with reasons + confidence | Assert without evidence |
| Run on Brain, read via Memory | Open its own DB connections |
| Degrade gracefully when unavailable | Block core manual workflows |

**Tiered models:** cheap/local for perception and structure; frontier for genuine
reasoning. Don't burn the expensive model on what a regex could do.

---

## XI. Pull request principles

Every PR is a statement about what Nova becomes. Review accordingly.

### Before you open it

- [ ] I can name the **user decision** this improves.
- [ ] I can point to the **ground truth** it reads or writes.
- [ ] I did not store anything **derived**.
- [ ] I did not cross a **boundary** the architecture tests police.
- [ ] I used **real SQLite** in tests for any persistence change.
- [ ] If I added a mutation, I added **event + invalidation** paths (or documented deferral).
- [ ] The diff is **as small as** the task allows.

### What reviewers owe the author

- **Clarity, not performance.** Review for correctness, boundaries, naming, and
  ten-year maintainability before bike-shedding style.
- **One blocking reason at a time.** Don't death-by-a-thousand-nits a good direction.
- **Name the anti-pattern** if you see one — use shared vocabulary from this doc.
- **Ask "what decision?"** for any new UI surface or metric.

### What authors owe reviewers

- A description that says **why**, not only what.
- Screenshots or examples for anything user-facing.
- Explicit callouts for debt, deferrals, and ADR needs.
- Gratitude for a blocked merge — it is cheaper than a production lie to the user.

### Merge bar

We merge when the code is **boring, bounded, tested, and honest** — not when it is
clever or complete in the abstract. "Works on my machine" is not a bar. Green CI +
human judgment is.

---

## XII. What we refuse to become

Knowing what Nova is not protects what it is:

- **Not a feature warehouse.** Linear + Notion + Jira + QuickBooks in one skin.
- **Not an engagement product.** Streaks, badges, nagging, infinite backlog anxiety.
- **Not a cloud surveillance app.** The user's life is not our training data exhaust.
- **Not an autonomous agent that acts first.** Trust is earned in small commits.
- **Not a science project.** No architecture astronautics; no rewrite fantasies.
- **Not a team tool in v1 clothing.** Single-operator excellence before multiplayer.
- **Not a document editor or code host.** We reference; we don't re-platform the world.

When a stakeholder (or your own enthusiasm) pushes toward one of these, this section
is the polite no.

---

## XIII. How to disagree — and how to change Nova

We freeze architecture so we can **build**, not so we can **stop thinking**.

If implementation proves the architecture wrong:

1. **Say so explicitly.** Name the failure mode with evidence.
2. **Stop.** Do not route around silently.
3. **Draft an ADR.** Propose; don't merge your workaround.
4. **Accept the human decision.** If rejected, implement inside the freeze.

Silent workarounds are how cultures decay — everyone optimizes locally until the
system is unrecognizable.

Good engineers fight the **problem**. Great engineers fight the problem **inside the
constraints** — and only reopen constraints when the cost of not doing so is real.

---

## XIV. Rituals that keep the culture alive

### The thirty-second test (product)

Open Nova. In thirty seconds, the founder must know: what matters today, what's
slipping, where time is wasted, which holding needs attention, whether the portfolio
is moving. If your work doesn't serve that, reconsider it.

### The two-a.m. test (engineering)

Read your diff as a stranger. No context, no Slack thread. Does it explain itself?
Would you trust it with your own data?

### The ADR test (architecture)

*"Would a future engineer reverse this thinking it was an accident?"* If yes, write
the ADR.

### The subtraction test (roadmap)

Before adding a gate, name what **won't** be built because you built this. Roadmaps
are choices, not wish lists.

---

## XV. Closing — the kind of engineers we hire

We hire people who:

- Find **boring** beautiful when it is **correct**.
- Feel physical discomfort at **duplicate sources of truth**.
- Ask **"what decision?"** before **"what table?"**
- Can **stop** when the architecture says stop — and **document** when they think
  it shouldn't.
- Treat the user's attention and privacy as **liabilities on our balance sheet** —
  something we owe back with interest, in the form of a product that actually helps
  them live and build.

Nova is built slowly on purpose. Domains are instruments. Ledgers are truth.
Derivation is respect for the user's time. Explanation is respect for their trust.

Build like the company depends on it — because for the founder running four
products and two clients on fifty hours a week, **it does**.

---

## Companion documents (read next, not instead)

| Document | Role |
|---|---|
| `CLAUDE.md` | Repo ground truth for agents and humans |
| `NOVA_ENGINEERING_HANDBOOK_v1.md` | How code is written (enforceable rules) |
| `docs/adr/` | Irreversible architectural decisions |
| `docs/workos/IMPLEMENTATION_GOVERNANCE.md` | WorkOS engineering laws |
| `NOVA_WORKOS_EXECUTION_MODEL_v1.md` | Why WorkOS exists — decision instrument |
| `tests/architecture/test_dependencies.py` | Boundaries as code |

*This document is living culture, not frozen law. Amend it rarely, deliberately,
and with the same ten-year horizon it describes — but never in a way that
contradicts accepted ADRs without superseding them.*
