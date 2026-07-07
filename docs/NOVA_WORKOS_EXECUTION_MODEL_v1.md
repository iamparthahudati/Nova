# Nova WorkOS — The Execution Model ("Finance for Execution")

**Status:** Product design. Quality bar: the Finance module. Frozen inputs
(unchanged, obeyed): the Objective·Type·Facet entity model, the architecture, the
data model, the Product Experience, and the UI spec. This document does **not**
redesign any of them — it designs the *domain* the way `FINANCE_DOMAIN.md` designed
Finance: what it is, what it derives, and every decision it exists to make.
**The test applied to every section:** *What decision does this help the founder
make?* If a surface, metric, report, or dashboard does not drive a decision, it is
cut. No exceptions.
**The feeling:** open WorkOS for 30 seconds and know — what matters today, what's
slipping, where time is wasted, which product deserves investment, which client
deserves attention, which commitments are at risk, and whether the company is
moving forward.

---

## The founding analogy: Finance for Execution

Finance is disciplined because it derives everything from a tiny ledger and never
lets the user hand-maintain a number. WorkOS copies that discipline exactly — the
asset is different (time and attention instead of money), the machinery is the same.

| Finance | WorkOS (Execution) |
|---|---|
| **Money** is the asset | **Attention** (time × focus) is the asset |
| Accounts — *where money lives* | **Holdings** — *where attention goes*: Products, Clients, Goals |
| Transactions — *every money movement* | **Two ledgers**: Commitments (intent) + Time (reality) |
| Balance — *derived, never stored* | Momentum & time-invested — *derived, never stored* |
| Financial health — derived | **Execution health** — derived |
| Net worth — asset − liability | **Return on Attention** — value produced ÷ time spent |
| Upcoming payments — obligations due | **At-risk commitments** — deliverables/deadlines slipping |
| Cash flow — where money flowed | **Time flow** — where attention actually went vs where it should |
| ROI | ROI (same math, on hours instead of rupees) |
| "Where's my money / what next?" | "What am I building / what today?" |

Finance answers 4 questions. WorkOS answers 8 — and every one is a **decision**:

| The founder's question | The decision it drives |
|---|---|
| What am I building? | Where to point the next hour |
| What should I work on today? | Today's allocation |
| What commitments are at risk? | What to rescue *now* |
| Which products are healthy? | Invest / maintain / pause / kill |
| Which freelance clients need attention? | Prioritize / update / renegotiate / fire |
| Where is my time actually going? | Stop the waste |
| Which work creates the highest ROI? | Double down |
| What should I stop doing? | Reclaim attention |

---

## 1. Core Philosophy

**WorkOS is a capital-allocation system for a founder's attention.** Time is the
only non-renewable capital; every product, client, and goal is a *position* that
consumes it and produces (or fails to produce) a return. WorkOS exists to make that
allocation legible and to drive better allocation decisions over time.

Four commitments, inherited from Finance and non-negotiable:

1. **Everything is derived; nothing is hand-maintained.** The founder never updates
   a status, drags a card, or sets a priority. Health, ROI, risk, priority, and
   "what's next" are **computed** from the two ledgers, exactly as Finance computes
   balance from transactions. A status you have to maintain is a status that rots.
2. **Every surface drives a decision.** Not a board to admire, not a metric to
   watch — a decision to make. If it doesn't, it's deleted.
3. **The AI is a chief of staff, not a task manager.** It proposes, explains, and is
   honest — including the uncomfortable "stop doing this." It is aligned to the
   founder's outcomes, not to engagement.
4. **Ruthless subtraction over feature breadth.** WorkOS is not Jira/Linear/Notion/
   ClickUp minus something. It is a *decision instrument* that happens to hold work.

**What decision does the philosophy drive?** Whether to trust WorkOS as the single
place that tells you where your attention should go — which it earns only by never
making you maintain it and always pointing at a decision.

---

## 2. Mental Model

The founder does **not** think in "tasks" or "tickets." They think:

> *"I'm running a portfolio — four products I'm building, some clients paying me now,
> and my own growth — and I have ~50 usable hours a week to spread across all of it.
> Where should this hour go, and what am I dropping?"*

So WorkOS's mental model is a **portfolio of attention**:

```
         ATTENTION (finite weekly capital)
                       │  allocated across
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
    PRODUCTS         CLIENTS          CAREER / PERSONAL
   (investment)    (cash now)        (future return)
   Nova            Acme              Learn Rust
   SplitEasy       BetaCo            Ship writing
   Moniqo          …                 Health
   DigiHealth
        │              │               │
        └──── each is a HOLDING with derived health + ROI ────┘
                       │
             produces RETURN (revenue, growth, learning)
```

- **Holdings** are the positions: Products, Clients, Goals. (Under the frozen model
  these are Objectives at the stream altitude, carrying the Value/Party/Outcome
  facets — but the founder just sees "my products / my clients / my goals.")
- **Commitments** are what you intend or owe within a holding (frozen: Work
  objectives). This is the **Commitment ledger** — the intent side.
- **Time** is where your hours actually went. This is the **Time ledger** — the
  reality side.
- **Health, ROI, risk, priority, allocation** are all *derived* from these three
  (holdings + the two ledgers) plus Finance's realized revenue.

**The two-ledger core** is the whole engine, and it's the Finance discipline exactly:
Finance reconciles what you *have* against what *moves*; WorkOS reconciles what you
**said you'd do** (Commitments) against what you **actually did** (Time). The gap
between them *is* the founder's most important signal — it reveals drift, waste, and
overcommitment before any dashboard does.

**What decision does the mental model drive?** It reframes every question from
"what's on my list?" to "where should my scarce attention go, and what's the return?"
— the only frame that leads to *stopping* things, not just doing more.

---

## 3. Information Architecture

Organized by **decision**, never by container. There is no project tree to navigate
(that's the filing-cabinet mistake). There are decision surfaces:

```
TODAY            → "What do I do now, and what's slipping?"        (daily decision)
STREAMS          → Products · Clients · Career                     (which holding?)
  └ HOLDING      → one product/client/goal: health, next, ROI      (invest/attend/stop?)
TIME             → where attention actually went + waste            (what to stop?)
FOUNDER          → portfolio health, allocation, ROI, momentum      (rebalance?)
REVIEWS          → weekly / monthly derived decisions               (reallocate?)
```

Everything rolls up cleanly: a **Commitment** belongs to a **Holding**, which sits in
a **Stream**, which rolls into the **Portfolio**. Health and ROI aggregate the same
way Finance rolls transactions → account → net worth. One number at the top ("is the
company moving forward?") decomposes all the way down to "this commitment is
slipping."

**What decision does the IA drive?** At every altitude, the *next* decision: portfolio
→ which stream to rebalance; stream → which holding to attend; holding → which
commitment to rescue or which to stop.

---

## 4. Daily Workflow

The loop, and its single daily decision — *"what are the 2–3 things that most move my
portfolio today, and what's about to break?"*

```
capture (all day, one line)  →  MORNING BRIEF (decide, 30s)  →  execute (time flows
into the Time ledger, effortlessly)  →  evening close (optional, 30s: loops closed,
tomorrow pre-decided)
```

- **Capture** is frictionless and everywhere; the founder never files. (Frozen UX.)
- **The Morning Brief** (§13) is the daily decision surface — derived, not built.
- **Execution** silently populates the Time ledger (the ground truth for everything).
- **Evening close** is optional; it closes open loops so nothing lives in the
  founder's head overnight (the Zeigarnik relief — a plan is a promise the brain can
  release).

**What decision does the daily workflow drive?** Today's allocation of attention —
and it must be answerable in 30 seconds, or the founder reverts to their head and
the app dies.

---

## 5. Product Workflow (building Nova, SplitEasy, Moniqo, DigiHealth)

A Product is a **holding you invest in for future return.** WorkOS does *not* show a
board of tickets. It shows a **product brief that reads like a Finance account
statement** — derived, decision-oriented:

```
Moniqo                         ● at-risk      invested 42h      exp ₹— · real ₹0
────────────────────────────────────────────────────────────────────────────────
Next meaningful ship: onboarding v1  (~3 weeks at current momentum)
Momentum: 6h/wk (needs ~12h to hit your target)     ⚑ slipping
Blocked: paywall design (waiting on you)
ROI signal: 42h in, ₹0 out, no revenue path defined → investment or zombie?
```

The founder runs a product by **capturing work against it**; WorkOS **derives** the
brief. Decisions each field drives:

| Field (derived) | Decision |
|---|---|
| Next meaningful ship + ETA | Is this close enough to justify a push? |
| Momentum vs needed | Am I giving it enough, or starving it? |
| Blocked | Is *my own* inaction the bottleneck? |
| Health band | Attend now, or leave it? |
| ROI signal (time in vs revenue path) | **Keep investing, or is this a zombie to pause?** |

**What decision does the product workflow drive?** For each product: *invest more /
maintain / fix / pause / kill* — the only decisions that matter for a solo founder
with four products and 50 hours. Everything else (columns, ticket counts, velocity
charts) is deleted because it drives none of those.

---

## 6. Freelancing Workflow (clients)

A Client is a **holding that pays cash now** — deadline-driven, relationship-managed,
the opposite profile from a product. Its brief is money- and risk-forward:

```
Acme — analytics dashboard          ● on-track    ROI ₹2,200/h    real ₹40k / ₹2L
────────────────────────────────────────────────────────────────────────────────
Owed: CSV export (due Fri) · pagination (due next Wed)
Deliverable risk: export 70% done, on pace ✓
Payment: ₹40k received, ₹1.6L outstanding (from Finance)
Relationship: last update 6 days ago → update due
```

Decisions each field drives:

| Field (derived) | Decision |
|---|---|
| Owed + due dates | What must I deliver, by when? |
| Deliverable risk (progress vs deadline) | **Which client is about to be let down — rescue now?** |
| Payment (from Finance) | Who owes me — chase? |
| ROI per hour | **Is this client worth my time, or should I fire them?** |
| Relationship recency | Do I owe an update? (Nova drafts it.) |

Products vs clients is the core distinction WorkOS must honor: **clients optimize for
delivered-on-time and ROI-per-hour (cash now); products optimize for momentum and
ROI-trajectory (investment).** Same holding machinery, different health and decision
lens.

**What decision does the freelancing workflow drive?** *Prioritize / send update /
renegotiate scope / fire* — and above all, *which client is at risk of a missed
deliverable this week.*

---

## 7. Time & Execution Model

The **Time ledger is WorkOS's `transactions` table** — the ground truth from which
allocation, ROI, and waste are derived. It answers the question founders are most
wrong about: *where is my time actually going?*

- Captured with minimal friction (a running timer, quick "worked 2h on Acme," or
  inferred from focus sessions) — never a mandatory timesheet.
- The decisive output is the **gap between stated priority and revealed allocation**:

```
This week — where attention actually went
Client   ████████████████  52%   (you said clients were secondary)
Product  ████████          28%   (Nova, your #1, got 12%)
Admin    ██████            15%   ⚑ waste candidate
Personal █                  5%   (Rust: 0h — 3rd week)
```

That single view drives the two highest-leverage decisions in the whole product:
**what to stop** (the 15% admin, the low-ROI client) and **what to protect** (the
starved #1 product). Finance shows you the ₹0-return 60-hour project; the Time model
is what makes that visible.

**What decision does the time model drive?** *Stop the waste; reallocate to the
starved high-value holding.* Revealed-vs-stated is the honesty engine — it's the
"you spent 62% on your lowest-ROI work" moment, made structural.

---

## 8. Health Model (the derived spine)

Every holding carries a **derived health band** — never set by hand, recomputed on
every read, exactly like Finance's derived statement status. The bands and their
decision:

| Band | Meaning | Decision |
|---|---|---|
| **Thriving** | ahead of pace, shipping, returning | Protect it |
| **Healthy** | on pace | Leave it alone |
| **At-risk** | slipping vs its own targets/deadlines | Attend this week |
| **Stalled** | no recent activity | Revive or consciously shelve |
| **Zombie** | high time, no return, no momentum | **Stop** |

Health inputs (all derived, all from the two ledgers + Finance):
momentum (recent progress vs needed) · commitment follow-through · slippage
(deadline vs progress) · staleness · blocked-by-me · ROI trend.

**Portfolio health** is the roll-up — the single answer to *"is the company moving
forward?"* — and it decomposes on tap to the exact at-risk holding and the exact
slipping commitment.

**What decision does the health model drive?** *Which holding needs my attention
right now* — and it must surface the answer without the founder asking, because a
health model you have to go check is a health model that doesn't work.

---

## 9. AI Chief of Staff Behavior

The chief of staff *is* the decision layer — everything above is the substrate it
reasons over. Its behavior, bounded:

- **Derives the daily brief** — ranks today's candidates by portfolio impact, not
  urgency-theatre, and explains each ("Nova onboarding — your #1 product, starved to
  12% this week").
- **Flags what's slipping** — a deliverable behind pace, a product losing momentum, a
  neglected client — *before* the founder notices.
- **Flags waste and drift** — the revealed-vs-stated gap; the admin sink; the zombie.
- **Proposes what to stop** — the hardest, most valuable output. An engagement-funded
  platform will never tell you to do less; an aligned chief of staff will.
- **Models the founder over time** — follow-through rate, estimation bias, revealed
  priorities, which past advice actually improved outcomes. This longitudinal model
  is what makes its judgment *yours*, and it compounds.
- **Speaks only when it earns it** — morning brief, a genuine risk moment, the weekly/
  monthly review. Silent otherwise. Every recommendation carries a *why* and a
  *confidence*.

**What decision does the chief of staff drive?** All of them — it is the layer that
converts the ledgers into ranked, explained, honest recommendations the founder
either accepts or overrides. Its quality *is* WorkOS's quality.

---

## 10. Dashboards (exactly two, each a decision surface)

No generic widget grids. Two dashboards, each opening with a **verdict and a lever**,
like Finance's dashboard opens with balances and the one thing due.

**Today** — the daily decision. (See §13, the Morning Brief; Today *is* the brief plus
the live day.)
- *Decision:* what do I do now, what's slipping.

**Founder** — the portfolio decision.
```
Is the company moving forward?           ▲ moving — 3 of 4 products advanced
────────────────────────────────────────────────────────────────────────────
Biggest lever: Nova starved (12% of time, #1 priority) → rebalance   [ Plan ]

Nova       ● healthy    ▲ shipping     12h   exp ₹—     highest strategic
Acme       ● healthy    on-track       26h   ₹2,200/h   paying
SplitEasy  ● healthy    maintenance     6h   live
Moniqo     ● at-risk    ⚑ 42h ₹0       42h   ₹0         zombie watch
Attention  client 52% · product 28% · admin 15% · personal 5%
```
- *Decision:* where to invest/divest attention this week; what to stop.

**What decision does each dashboard drive?** Today → the next hour. Founder →
the next week's allocation and the next thing to kill. If a proposed dashboard
doesn't map to one of those two decisions, it isn't built.

---

## 11. Reports

Reports are **periodic derived narratives that force periodic decisions** — never
archives of charts. There are exactly two (§14, §15), and each *ends in a
recommendation the founder accepts or overrides*, not a wall of stats. A report that
doesn't propose a decision is deleted.

**What decision does a report drive?** Reallocate attention for the next period; stop
or double down on a holding. If it only informs, it's cut.

---

## 12. KPIs

Every KPI is decision-linked; vanity metrics (task counts, raw velocity, hours-logged-
for-their-own-sake) are **banned** because they drive no decision.

| KPI | Derived from | Decision it drives |
|---|---|---|
| **Return on Attention** (north star) | value ÷ time, portfolio-wide | Is my time producing more of what matters? |
| **Follow-through rate** | Commitment vs Time ledger | Am I keeping my promises to myself? (leading trust metric) |
| **Attention allocation vs intent** | Time ledger vs stated priority | What to stop / protect |
| **ROI per hour, per holding** | Time + Finance | Which product/client deserves the hour |
| **Momentum, per product** | recent progress vs needed | Invest or starve |
| **At-risk commitment count** | deadlines vs progress | What to rescue today |
| **Waste %** | low-return time / total | What to cut |

**What decision does each KPI drive?** Named in the table — and if a proposed metric's
"decision" column is blank, it does not ship. This is the Finance discipline: numbers
exist to be acted on.

---

## 13. Morning Brief (the hero surface)

The 30-second daily decision, fully derived, delivered before the founder asks:

```
Tuesday · Good morning.

Focus today (ranked by portfolio impact)
1 ▸ Nova onboarding — your #1 product, starved to 12% this week      why ⌄
2 ▸ Acme CSV export — due Fri, ₹40k, blocks their sign-off            why ⌄
3 ▸ SplitEasy 3-way bug — small, aging a week                         why ⌄

At risk
⚑ Acme pagination (due Wed) — not started
⚑ Moniqo — 3rd week slipping; 42h invested, ₹0 path

One honest thing
You said Nova was #1. It got 12% of last week. Protect a Nova block?   ✓ / not now
```

It answers, in one glance: **what matters today** (focus), **what's slipping** (at
risk), and **the honest nudge** (drift/stop). This is the surface that makes the
founder open WorkOS every morning — the brief is the daily reason to return, and it's
*derived*, so it's never stale or wrong-because-unmaintained.

**What decision does the Morning Brief drive?** Today's allocation, and the one loop
about to break. It is the single most important surface in WorkOS; if it isn't right,
nothing else matters.

---

## 14. Weekly Review

A derived retrospective that forces one decision: **how to reallocate next week.**

```
Your week · 30 Jun – 6 Jul
Shipped: Acme export, SplitEasy bug, Moniqo onboarding v1.
Attention went: client 52% · product 28% · admin 15% · personal 5%.
Drift: Nova (#1) got 12%. Rust: 0h (3rd week). Admin 15% — mostly invoicing.
Health moves: Moniqo → at-risk (zombie watch). Acme steady.

Next week I'd: protect two Nova mornings, cap clients at 40%, batch admin to
Friday. Decide on Moniqo — invest or shelve?           [ Accept ] [ Adjust ]
```

**What decision does the Weekly Review drive?** Next week's attention allocation, plus
one explicit *stop/continue* call (here: Moniqo). It seeds Monday's brief.

---

## 15. Monthly Review

The **portfolio capital-allocation review** — the founder's monthly board meeting with
themselves. It forces the biggest decisions:

```
Your month · June
Portfolio: 4 products, 2 clients. Return on Attention ▲ vs May.
Products: Nova ▲ (but under-fed) · SplitEasy → maintenance · Moniqo ⚑ 60h/₹0 ·
          DigiHealth still idea-only (0 progress 2 months).
Clients: Acme ₹2,200/h ✓ · BetaCo ₹600/h — below your floor.
Career: Rust stalled. Writing: 0.

Recommendations:
• Shelve or hard-commit Moniqo — 60h/₹0 is a zombie.        [ decide ]
• Renegotiate or drop BetaCo — below your hourly floor.     [ decide ]
• DigiHealth: kill the idea or schedule a real spike.       [ decide ]
• Protect Nova — your ROI leader by strategic weight.
```

**What decision does the Monthly Review drive?** The portfolio calls a solo founder
avoids and shouldn't: *kill/pause a product, fire a client, revive or bury a stalled
bet, double down on the leader.* This is where WorkOS earns its keep as decision
infrastructure, not a task app.

---

## 16. ROI Model

The economic engine, mirroring Finance's exactness. **ROI = value produced ÷ time
invested**, per holding, rolled to the portfolio as **Return on Attention.**

- **Time invested** — from the Time ledger (exact, integer minutes; the Finance
  never-use-floats discipline).
- **Value** —
  - *Clients:* realized revenue (read from **Finance** at the facade — never
    re-stored; the frozen cross-domain seam) + outstanding expected.
  - *Products:* expected revenue path + realized (Finance) + strategic weight
    (from linked Goals) — a product with no revenue *yet* isn't ₹0 value; it's
    weighted by the goal it serves, so investment reads correctly.
  - *Career/Personal:* non-monetary — progress toward the linked Goal, weighted by
    how much the founder said it matters.
- **The honest outputs:** ROI-per-hour ranks clients (fire the floor); ROI-trajectory
  ranks products (invest in the climber, shelve the flat); Return on Attention tells
  the founder whether their *whole* allocation is improving.

**What decision does the ROI model drive?** *Which work to double down on and which to
stop* — the highest-leverage decisions a founder makes, and the ones no calendar or
todo app can inform because they lack the Time ledger × Finance fusion.

---

## 17. Product Health Model

Health specific to *investments* (products), derived, banded for one decision:
*invest / maintain / fix / pause / kill.*

| Input (derived) | What it detects |
|---|---|
| Momentum (ship cadence vs needed) | Is it advancing fast enough to matter? |
| Distance to next meaningful ship | Is it close enough to push? |
| Time-burn vs value/strategic weight | Is investment justified? |
| Staleness | Has it quietly died? |
| ROI trajectory | Climbing, flat, or zombie? |

**Zombie detection is the signature output:** high cumulative time + no revenue path +
flat momentum → an explicit *stop* candidate (Moniqo at 42h/₹0). Founders keep zombies
alive out of sunk-cost; WorkOS names them.

**What decision does product health drive?** For each product, one of five: invest,
maintain, fix, pause, kill — and it proactively surfaces the *kill/pause* candidates
the founder is emotionally avoiding.

---

## 18. Client Health Model

Health specific to *cash-now relationships*, derived, banded for one decision:
*prioritize / update / renegotiate / fire.*

| Input (derived) | What it detects |
|---|---|
| Deliverable risk (progress vs deadline) | About to let this client down |
| ROI per hour | Below your hourly floor → unprofitable |
| Payment status (from Finance) | Owes you → chase |
| Relationship recency | Gone quiet → update due |
| Scope creep (committed vs original) | Doing free work |

**What decision does client health drive?** *Which client is at risk of a missed
deliverable this week* (rescue), and *which client is quietly unprofitable* (renegotiate
or fire). The two decisions that protect a freelancer's reputation and rate.

---

## 19. Decision Engine (the synthesis)

WorkOS is, at its core, a **decision engine.** The two ledgers + holdings + Finance
feed the chief of staff, which outputs ranked, explained decisions. Every surface in
this document maps to exactly one founder decision:

| Founder decision | Fed by | Surface |
|---|---|---|
| What to do now | Commitments × health × impact | Morning Brief / Today |
| What to rescue | Deadlines vs progress | At-risk (Brief, client/product health) |
| What to stop | Time ledger × ROI × zombie detection | Time model, Reviews, health |
| Which product to invest in | Product health × ROI trajectory | Product brief, Founder |
| Which client to attend/fire | Client health × ROI/hr | Client brief, Founder |
| Where time is wasted | Revealed vs stated allocation | Time model |
| Is the company moving | Portfolio health roll-up | Founder dashboard |
| How to reallocate | All of the above, periodic | Weekly / Monthly Review |

The engine's discipline: **inputs are ground truth (never opinions the founder must
maintain); outputs are decisions (never data the founder must interpret).** That is
the entire difference between WorkOS and a project-management tool — and it is the
same difference between Finance and a spreadsheet of transactions.

**What decision does the decision engine drive?** It *is* the decisions — it exists to
convert two ledgers into the eight founder decisions, ranked and explained, with the
founder as the final approver.

---

## 20. Future Scalability

Designed-for, not built now — the portfolio model scales without reshape:

- **More products/clients (tens → hundreds):** the portfolio/health/ROI roll-up is
  built for aggregation; a founder with 20 products still gets one Founder verdict and
  a ranked list of what needs attention. Breadth increases the *value* of derivation,
  not the founder's burden.
- **Solo → team:** assignment is a facet on a commitment (frozen model + reserved
  `owner_id`); the ledgers and health models are unchanged — a teammate is another
  source of Time and Commitment entries. WorkOS becomes the team's *operating
  cadence* without becoming a new product.
- **Deeper behavioral model over time:** follow-through, estimation bias, revealed
  priorities, advice-efficacy — the chief of staff's judgment compounds and
  personalizes, which is the durable moat, not a feature.
- **The company operating layer (later):** portfolio-of-attention → org's execution
  intelligence is the natural expansion, and it inherits every model here unchanged.

**What decision does scalability drive?** What to *refuse* now: no team features, no
company mode, no integrations-as-dependency in v1. WorkOS earns the right to expand by
first being the indispensable execution instrument for one founder — the Finance
sequencing exactly.

---

## Non-goals (what WorkOS refuses to be)

Stated plainly, in the Finance-doc tradition, because subtraction is the product:

- **Not a board/kanban tool.** Columns of cards make *the founder* synthesize status;
  WorkOS derives it. No board is the hero surface.
- **Not a backlog.** An infinite list of someday-tasks is anxiety, not decision
  support. WorkOS holds commitments and surfaces the few that matter.
- **Not a sprint/ceremony system.** No planning poker, no velocity ritual, no
  stand-up. The founder plans by reviewing a derived brief, not by running Scrum.
- **Not a time-tracking compliance tool.** The Time ledger exists to drive ROI and
  waste decisions, never to police hours.
- **Not a document/wiki.** Knowledge lives in the Knowledge Graph (frozen); WorkOS
  references, never re-hosts.
- **Not a metric museum.** Every number drives a decision or it's cut.

---

## The 30-second test (the acceptance criterion)

Open WorkOS. Within 30 seconds the founder must know, without asking:

1. **What matters today** — top of the Morning Brief.
2. **What's slipping** — the At-risk block.
3. **Where time is wasted** — the allocation strip (admin 15%, zombie hours).
4. **Which product deserves investment** — Founder health + the starved-#1 lever.
5. **Which client deserves attention** — client health / deliverable risk.
6. **Which commitments are at risk** — At-risk, with due dates.
7. **Whether the company is moving forward** — the Founder verdict line.

If any of these takes longer than a glance, the design has failed the Finance bar and
is wrong. That single test governs every future WorkOS decision — the same way
"derived, never stored" governed Finance.
