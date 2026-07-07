# Nova WorkOS — UI/UX Specification v1 (Canonical)

**Status:** Canonical product design. Frozen inputs: the Architecture, Data/Entity
model (Objective · Type · Facet), and the Product Experience Vision. This document
designs the *surfaces* — navigation, screens, interactions, motion, keyboard. It
contains **no implementation, no code, no CSS, no schemas.** Wireframes are design
artifacts (spatial sketches), not markup.
**Voice:** Apple Human Interface team × Anthropic product. Calm, opinionated,
first-principles.
**How to use this document:** Part I locks the **design principles**. Every screen in
Parts III–V is designed against them and audited in the **compliance matrix**
(Part VII). No new screen ships without passing that matrix — this is how Nova stays
coherent for ten years.

---

# PART I — Design Principles (locked)

These are the filter. Every pixel, every shortcut, every animation is evaluated
against them. They are ordered; when two conflict, the lower number wins.

| # | Principle | The rule (testable) | It rejects |
|---|---|---|---|
| **1** | **One primary action per screen.** | You can name the screen's single most important action in one verb. If you can't, redesign. | Dashboards with ten equal buttons. |
| **2** | **Every screen answers "What should I do next?"** | No screen is pure data. Every surface points to an action Nova recommends. | Read-only reports, static boards. |
| **3** | **Calm by default, depth on demand.** | ≤7 primary items visible. The many are revealed only when asked. | Walls of cards, infinite backlogs. |
| **4** | **Keyboard-first, mouse-second, voice-equal.** | Every action reachable in ≤2 keystrokes or one sentence to Nova. Mouse is never *required*. | Mouse-only drag rituals. |
| **5** | **Two interactions to anything.** | Nothing is more than two clicks — or one command — deep. | Nested menus, buried settings. |
| **6** | **AI explains everything it recommends.** | Every ranking, plan, estimate, and score has a "why" one interaction away, with its confidence. | Black-box priority numbers. |
| **7** | **The user corrects, never constructs.** | Screens open in Nova's *proposed* state (a good guess), editable — never a blank form. | Empty "New Project" modals with 9 fields. |
| **8** | **Silence is designed.** | No badge counts, no notification spam. Interruptions are earned (time-critical, user-requested, or a trusted auto-action). | Red dots, nagging. |
| **9** | **Empty states teach the next action.** | Never "nothing here." Always "here's how to start," with the action focused. | Apologetic blank screens. |
| **10** | **Motion explains causality, never decorates.** | Every animation shows where something came from or went. If it's only pretty, cut it. | Confetti, bounce-for-fun. |
| **11** | **One anatomy everywhere.** | A project, a goal, a client share the same page skeleton — learn one, know all. | Bespoke layouts per feature. |

**The meta-test for any decision:** *Does this make the user do less organizing and
feel more certain about what matters?* (The north star from the Experience Vision.)

---

# PART II — The Design System (experiential foundations)

Not visual specs — the *felt* language every screen inherits.

### The canvas
A single **column of attention**, centered, generous whitespace, one focal region.
Optional **right rail** for Nova's reasoning and context — collapsible, never
demanding. No dense multi-pane cockpits. The screen breathes. Dark and light are
equal citizens; dark is the default for a tool you live inside at night.

```
┌───────┬──────────────────────────────────────────┬─────────────┐
│       │                                          │             │
│ side  │        the column of attention           │  Nova rail  │
│ bar   │        (one focal region, calm)          │  (optional, │
│(lenses│                                          │  reasoning) │
│  ≤7)  │                                          │             │
│       │                                          │             │
└───────┴──────────────────────────────────────────┴─────────────┘
        └────────── ⌘K palette · ⌘N capture · ⎵ talk ──────────┘
```

### The three input surfaces (the whole interaction model)
1. **Sidebar — navigate.** *Lenses*, not contents (Part III). How you change *what
   you're looking at*.
2. **Command Palette (⌘K) — do & ask.** The universal verb surface: go anywhere,
   command anything, ask Nova anything. The keyboard heart.
3. **Capture (⌘N, or hold ⎵ / "Hey Nova" — talk).** The frictionless one-line create
   from anywhere. Distinct from the palette by *intent*: capture *creates/dumps*; the
   palette *navigates/commands*.

### Nova's presence
Nova is **a calm presence, not a chatbot bubble.** It appears as (a) the **right
rail** (reasoning, proposals, the day's changes), (b) inline **"why" chips** on
anything it recommends, and (c) the **briefing** surface. Conversation is
first-class but never a gimmicky floating widget in the corner. When Nova has
nothing time-critical, it is *invisible*.

### Motion language
Spring-based, quick (150–250ms), **origin-aware**: things grow from where they came
and collapse to where they go. Completing work makes the next thing *rise*. Re-plans
use shared-element motion so you *see* what moved. Nothing bounces for fun.

### Color as meaning, not decoration
A restrained neutral canvas, **one accent** for the primary action, and semantic
color used *only* for health and risk (on-track / at-risk / off-track). If color
isn't carrying meaning, it isn't there.

---

# PART III — Navigation & Shell

### The Sidebar — *lenses, not contents*

The single most important navigation decision, and where every competitor gets it
wrong: **the sidebar shows ways of looking, never the list of your objects.** Jira,
Notion, ClickUp cram a growing tree of projects/pages into the sidebar — it becomes a
filing cabinet you scroll. Nova's sidebar is a fixed, tiny set of **lenses** (≤7,
Principle 3):

```
┌──────────────┐
│  ◐  Today     │  ← home; the default lens
│  ▤  Work      │  ← all projects & products, as a calm list
│  ◎  Goals     │
│  ⧉  Clients   │  ← freelancing / engagements
│  ₹  Finance   │  ← the existing Finance domain
│  ▦  Founder   │  ← the whole-life dashboard
│ ─────────────│
│  ⟲  Review    │  ← weekly/monthly reflection
│  ⚙  Settings  │  ← the trust console
│              │
│  ✦ Nova       │  ← toggle the reasoning rail / talk
└──────────────┘
```

- **Purpose:** change *what you're looking at* in one keystroke, without ever
  scrolling a tree.
- **Primary action:** jump to Today (always the fastest path home).
- **Interactions:** click or `⌘1…⌘7` to switch lens. Collapsible to icons (⌘\).
  It **never grows** as you add projects — projects live *inside* the Work lens, found
  by ⌘K, not pinned to the rail.
- **Empty state:** fully populated from day one (lenses are fixed); no empty sidebar
  ever.
- **AI behavior:** a lens shows a subtle **dot** only when Nova has something
  time-critical there (earned attention, Principle 8) — never a count.
- **Keyboard:** `⌘1`–`⌘7` lenses; `⌘\` collapse; `⌘K` palette; `⌘N` capture.
- **Animation:** lens switch is an instant cross-fade with a 1px active-rail slide —
  causality (you moved), not spectacle.
- **Why better:** Linear's sidebar is teams/projects (grows, scrolls); Notion's is an
  infinite page tree (the filing cabinet); ClickUp's is a spaces/folders labyrinth.
  **Nova's sidebar has a fixed size forever** — cognitive load never increases as your
  work does. That is the whole point.
- **Challenge / rejected:** pinning favorite projects to the sidebar (starts the
  cabinet creep); a project tree (Jira's mistake); a "+" that creates top-level things
  (creation belongs to capture, not navigation).

---

# PART IV — The Screens

Each screen: **Purpose · Primary action · Information hierarchy · Layout ·
Interactions · Empty state · Loading state · AI behavior · Keyboard · Animation · Why
better · Challenge.**

## 1. Today (home)

- **Purpose:** answer *"what do I do now, and why,"* and let you commit to the day in
  seconds.
- **Primary action:** **Start the top thing** (Principle 1).
- **Information hierarchy:** ① The one thing / now → ② Today's shape (3–5 planned
  blocks) → ③ "On your mind" (one deadline, one risk, one nudge) → ④ quiet footer
  ("what Nova handled overnight").
- **Layout:** a centered column that reads like a morning note, not a grid.

```
   Tuesday, 7 July · Good morning.

   ▸ NOW  Acme CSV export                              [ Start ⏎ ]
     due Fri · ₹40k · blocks their sign-off              why ⌄

   Today
   ─ 09:00  Deep work — Acme export        2h   why ⌄
   ─ 11:30  SplitEasy 3-way split bug      45m  why ⌄
   ─ 14:00  Moniqo review                  1h   why ⌄

   On your mind
   ⚑ Rust: 0h in 2 weeks — protect Thu AM?     ✓ / dismiss

   ‹ Nova moved the Moniqo review here — you were over capacity ›
```

- **Interactions:** `⏎` starts the top item (enters Focus). `J/K` move selection;
  `1–5` jump to a block; drag to reorder *or* say "move deep work to the morning";
  `✓` completes and the next rises; **any "why ⌄" expands Nova's reasoning inline**
  (Principle 6).
- **Empty state (teaches):** *"Tell me what's on your plate and I'll shape your
  day,"* with the capture line focused and one example ghosted. Never "no tasks."
- **Loading state:** the plan **assembles top-down** — blocks slide in priority order
  as Nova "thinks," resolving from a skeleton. No spinner (motion = cognition).
- **AI behavior:** the day is **already planned** before you arrive (Principle 7);
  Nova notes what it changed and why in the footer, then goes silent.
- **Keyboard:** `⏎` start · `C` capture · `P` re-plan · `R` reflect · `⌘K` palette.
- **Animation:** completing a block collapses it and floats the next up (causality);
  a re-plan gently re-sorts with shared-element motion so you *see* the change.
- **Why better:** Jira/Linear home = a board (inventory → anxiety). Notion = a blank
  page. Motion = an auto-filled calendar grid you still manage. Sunsama = a *manual*
  daily-planning ritual where you drag tasks in. **Nova's home is a decision that's
  already been made and explained — you approve, you don't build.** It's the only
  "home" that is an answer, not a database.
- **Challenge / rejected:** a widget dashboard (no primary action, Principle 1); the
  full backlog (Principle 3, anxiety); a calendar-grid-first home (that's Motion's
  construction tax — the calendar is depth-on-demand, not the front door).

## 2. Command Palette (⌘K)

- **Purpose:** do or ask *anything* from anywhere, by keyboard.
- **Primary action:** execute the top-matched intent.
- **Information hierarchy:** your query → best action first → then navigate targets →
  then "Ask Nova" fallback (natural-language questions & commands).
- **Layout:** a centered floating bar over a dimmed canvas; results in one ranked
  list; a subtle mode hint (`navigate · command · ask`).

```
   ┌────────────────────────────────────────────┐
   │  ⌘K   plan tomorrow morning for deep work   │
   ├────────────────────────────────────────────┤
   │  ⚡ Plan tomorrow — protect AM for deep work │  ⏎
   │  ▤ Go to Moniqo                             │
   │  ◎ Goal: Learn Rust                          │
   │  ✦ Ask Nova: "how's Acme doing?"             │
   └────────────────────────────────────────────┘
```

- **Interactions:** type intent (fuzzy); `⏎` runs top; `⌘⏎` runs as "Ask Nova"; `↑/↓`
  select; `Esc` dismiss. It blends **command** (Linear-grade verbs) with
  **conversation** (ask a real question) in one surface.
- **Empty state:** on open (no query) it shows *recent + suggested* commands
  ("Plan today," "Review week," "Go to Founder") — teaches the verbs.
- **Loading:** "Ask Nova" answers **stream** into an inline answer card; commands
  execute optimistically.
- **AI behavior:** ranks intents by context (time of day, current lens); for
  questions, answers with a "why"/source and confidence.
- **Keyboard:** `⌘K` open; `⌘⏎` force-ask; `Tab` cycle mode.
- **Animation:** palette springs from center (fast), dims canvas; results re-rank
  live with quiet reordering.
- **Why better:** Linear's palette is commands-only; Notion's is search-only; neither
  *answers questions or plans*. Nova's palette is **one surface for do + go + ask** —
  the keyboard heart of an AI OS.
- **Challenge / rejected:** separate "search" and "command" and "chat" surfaces
  (three shortcuts to remember — collapse to one, Principle 5).

## 3. Capture (⌘N / hold ⎵ / "Hey Nova")

- **Purpose:** get a thought out of your head and perfectly filed in under two
  seconds, with zero organizing.
- **Primary action:** **Capture** (the thought lands placed & decorated).
- **Information hierarchy:** your sentence → Nova's live understanding (a chip row) →
  confirm/fix.
- **Layout:** a single line, focused, that **shows what Nova understood as you type**:

```
   ┌────────────────────────────────────────────────────────────┐
   │  Build CSV export for Acme, ~4h, due Friday, worth 40k      │
   └────────────────────────────────────────────────────────────┘
      Task · Acme ⧉ · Fri (hard) · 4h · ₹40k          [ fix ⌄ ]  ⏎
```

- **Interactions:** type or talk; the **parse preview** updates live (type, client,
  deadline, estimate, value, where it filed); `⏎` accepts; `fix ⌄` opens the *only*
  editable surface — and even that is pre-filled (Principle 7). Voice: hold `⎵`, speak,
  release.
- **Empty state:** a rotating ghost example ("try: 'call the DigiHealth designer
  tomorrow, 30m'") — teaches natural capture.
- **Loading:** parsing is instant/optimistic; the chip row settles as Nova confirms
  placement.
- **AI behavior:** extracts type + facets + placement; **shows its work** (the chips
  are the "why"); if unsure where to file, it *asks in one tap* rather than guessing
  silently.
- **Keyboard:** `⌘N` capture; `⎵` (hold) talk; `⏎` accept; `⌘Z` undo the last
  capture.
- **Animation:** on accept, the capture **flies to its home lens** (a 200ms
  shared-element arc) so you *see* where it went — then you're back where you were.
- **Why better:** every other tool makes capture a *form* (Jira, ClickUp) or a *dumb
  inbox you must triage later* (Things, Todoist). Nova **captures, places, and
  decorates in one gesture** — the triage never happens because it's already done.
- **Challenge / rejected:** a capture inbox that piles up (defers the organizing tax
  instead of removing it); a type/project picker before you can type (friction before
  thought).

## 4. Planning flow

- **Purpose:** review & commit the day (or week) — adjust by nudge, not by
  construction.
- **Primary action:** **Commit the plan.**
- **Information hierarchy:** the proposed plan on your real calendar → a capacity
  read → the reasons → the nudge line.
- **Layout:** the proposed timeline merged with calendar busy-blocks; a slim
  **capacity meter**; each block carries its "why."

```
   Tomorrow · capacity ▓▓▓▓▓▓▓░░  planned 6h of 7h

   09:00 ─ Deep work: Acme export   2h   ✦ deadline + revenue
   11:00 ─ (Standup — calendar)     30m
   11:30 ─ SplitEasy bug            45m   ✦ small, aging
   14:00 ─ Rust                     1h    ✦ you asked to protect this
          ────────────────────────────────
          “move deep work later” · “I’m low energy” ▸        [ Commit ⏎ ]
```

- **Interactions:** drag a block *or* nudge by voice/text ("push deep work to the
  afternoon," "I'm low-energy, give me lighter wins") → Nova re-flows instantly. The
  capacity meter turns amber if you over-commit (surfaced, never blocked). `⏎`
  commits.
- **Empty state:** if nothing's scheduled, Nova drafts from the priority queue and
  says so — you're reviewing, never starting from zero (Principle 7).
- **Loading:** blocks lay onto the timeline in sequence (the plan "settling").
- **AI behavior:** proposes the whole plan with reasons + confidence; **re-plans
  live** when reality changes (a meeting overruns) and leaves a one-line trace.
- **Keyboard:** `P` open planning; `⏎` commit; `[`/`]` shift a block; `A` accept
  Nova's suggestion.
- **Animation:** re-flows use shared-element motion — blocks *slide* to new times so
  the change is legible (Principle 10).
- **Why better:** Motion auto-schedules but hands you a **grid to manage**; Sunsama
  makes you **drag every task in by hand** each morning. Nova makes planning a
  **30-second review of a plan that already exists and explains itself**, and then
  *maintains it for you* through the day. Construction → curation.
- **Challenge / rejected:** an empty calendar you fill (Sunsama's ritual); rigid
  auto-scheduling with no "why" and no easy override (opaque, Principle 6).

## 5. Project experience

- **Purpose:** know a project's state and its next move **without reading a board.**
- **Primary action:** **Do the next action** (or ask "what's the status").
- **Information hierarchy:** ① plain-language status + health → ② next actions / the
  one blocker → ③ money & time (expected/realized ₹, hours, ROI) → ④ structure
  *on demand*.
- **Layout:** a **project page that reads like a brief**, not a board.

```
   Moniqo                                    ● at-risk    ₹0 / ₹0
   ────────────────────────────────────────────────────────────
   ✦ Behind pace. Core sync works; onboarding is the critical
     path, ~3 weeks out. Risk: no design for the paywall screen.

   Next
   ▸ Wire onboarding step 2        ▸ Decide paywall copy
   ⚑ Blocked: paywall design (waiting on you)

   Effort 42h · Expected —  · [ Structure ⌄ ]   [ Do next ⏎ ]
```

- **Interactions:** `⏎` starts the next action; **"Structure ⌄"** reveals the recursive
  outline (sub-work, dependencies) — *only when asked* (Principle 3). Because the
  underlying model is one fluid structure, reorganizing in the outline never breaks
  anything. Ask Nova inline: "why at-risk?" → the health reasons expand.
- **Empty state (new project):** Nova's proposed structure from your capture, not a
  blank page — "Here's how I'd break this down; adjust anything" (Principle 7, 9).
- **Loading:** the status narrative streams first (the answer), structure lazy-loads
  under the reveal.
- **AI behavior:** writes the status you'd otherwise write; scores health with
  reasons + confidence; surfaces the *one* blocker, not twenty.
- **Keyboard:** `⏎` do next · `S` structure · `?` why (health) · `U` draft update.
- **Animation:** the structure reveal *expands downward* from the "Structure" chip
  (origin-aware); health pill color-shifts smoothly on recompute.
- **Why better:** Jira/Linear = a board of issues you assemble into a story yourself;
  Notion = a doc you maintain by hand. **Nova writes the story for you; the board is
  optional depth.** You read a project in five seconds instead of interpreting a
  column of cards.
- **Challenge / rejected:** a Kanban board as the default project view (makes *you*
  synthesize status); a mandatory sub-task hierarchy (structure is optional here).

### 5a. Client / Engagement (a variant of the same anatomy — Principle 11)

Same page skeleton, tuned for freelancing: header carries **what you owe, by when,
worth, and ROI-per-hour**; body adds a **relationship strip** (last contact,
outstanding) and a one-tap **"Draft client update"** (Nova writes it from the week's
real activity). Primary action: **Draft update** or **Do next deliverable.** Why
better: no tool fuses CRM + delivery + money per client; Nova makes freelancing feel
like a *managed book of business.*

## 6. Goal experience

- **Purpose:** see whether you're **actually moving** toward what matters — and
  connect daily work to it.
- **Primary action:** **Protect time / adjust** toward the goal (accept a Nova
  suggestion).
- **Information hierarchy:** ① trajectory (on pace vs behind) → ② contributors →
  ③ drift alert.
- **Layout:** a **pace line**, not a task list — needed-rate vs actual-rate over time.

```
   Learn Rust · this quarter                         ● behind
   ────────────────────────────────────────────────────────────
        needed ╱
              ╱ ─ ─ ─ ─ ─ ─ ─ ─
             ╱        ● you are here (behind pace)
   ─────────╱─────────────────────────────────────────
   Contributing: “Rust track” (4h logged) · Nova book (0h)

   ⚑ 0 hours in 2 weeks. Protect Thursday mornings?   [ Protect ⏎ ]
```

- **Interactions:** `⏎` accepts Nova's time-protection suggestion; tap a contributor
  to jump to it; ask "what would get me back on pace?" → Nova proposes a concrete
  plan.
- **Empty state:** *"What outcome do you want, and by when?"* — one sentence; Nova
  proposes measurable key results (Principle 7, 9).
- **Loading:** the pace line draws in (needed first, then actual) — the gap is the
  point.
- **AI behavior:** computes trajectory + confidence; **flags drift honestly** and
  proposes a fix, tying daily work to the goal automatically.
- **Keyboard:** `⏎` accept suggestion · `?` why behind · `G` go to top contributor.
- **Animation:** the "you are here" marker eases along the actual line; on protecting
  time, a block visibly *appears* on the plan (cross-surface causality).
- **Why better:** Notion/Jira OKRs are static tables you update quarterly and ignore.
  **Nova's goal is live gravity** — it pulls on the priority queue and tells you when
  you've stopped walking toward it.
- **Challenge / rejected:** a % progress bar (hides whether you're on *pace*); a goal
  as a folder of tasks (loses the outcome).

## 7. Founder dashboard

- **Purpose:** answer *"how is everything?"* across the whole life — and point at the
  single biggest lever. **This is not a grid of charts** (explicitly rejected).
- **Primary action:** **Act on the top lever** (the at-risk project / the ROI
  outlier).
- **Information hierarchy:** ① one-line portfolio **verdict** → ② the top lever
  (recommended action) → ③ per-product/stream health + ROI → ④ where your hours
  actually went.
- **Layout:** a **narrated executive summary**, numbers attached to a "so what."

```
   Your book of work                              Q3 · week 2
   ────────────────────────────────────────────────────────────
   ✦ 4 active, 1 at risk. You’re over-indexed on client work:
     62% of hours, lowest ROI. Nova is the goal you named #1.

   ▸ Biggest lever: rebalance next week toward Nova   [ Plan it ⏎ ]

   Nova        ● on-track   38h   exp ₹—    ● highest strategic
   Acme        ● on-track   26h   ₹2,200/h  ● paying, low-strategic
   SplitEasy   ● healthy     6h   live
   Moniqo      ● at-risk    42h   ₹0        ⚑ 60h, no revenue yet

   Hours this week ▓▓▓▓▓▓ client ▓▓▓ product ▓ personal
```

- **Interactions:** `⏎` on the lever → Nova drafts next week's rebalanced plan; click
  any product → its Project page; ask "why is Moniqo at risk?" inline.
- **Empty state:** for a new user, teaches by showing the *shape* it will fill — "as
  you work, this becomes your whole-life command view."
- **Loading:** the verdict streams first (the answer), then rows resolve.
- **AI behavior:** **leads with a verdict and a recommended action** (Principle 2),
  every metric carrying a "so what"; states uncertainty on forecasts.
- **Keyboard:** `⏎` act on lever · `1–4` jump to a product · `?` explain a row.
- **Animation:** health pills settle after recompute; the hours bar fills left-to-
  right once (calm, not looping).
- **Why better than generic dashboards:** a normal dashboard is a wall of widgets that
  makes *you* find the insight. **Nova's founder view opens with the insight and the
  next move** — it's a chief-of-staff briefing, not a BI tool. Every number answers
  "so what should I do?"
- **Challenge / rejected:** a customizable widget grid (no primary action, no
  verdict); vanity charts with no recommendation (Principle 2).

## 8. Review flow (weekly / monthly)

- **Purpose:** a reflection that **writes itself** and seeds the next period.
- **Primary action:** **Accept next period's focus** (commit forward).
- **Information hierarchy:** ① what you shipped → ② where your hours actually went →
  ③ what's at risk next → ④ Nova's proposed focus for next week.
- **Layout:** a generated narrative + an editable "next week" you accept.

```
   Your week                                    30 Jun – 6 Jul
   ────────────────────────────────────────────────────────────
   Shipped: Acme export, SplitEasy bug, Moniqo onboarding v1.
   Time went: 62% client, 30% product, 8% personal.
   Drift: Rust (0h). Moniqo slipped 3 days.

   Next week, I’d protect Nova mornings and cap client to 40%.
                                        [ Edit ] [ Accept & seed ⏎ ]
```

- **Interactions:** read (30s); `Edit` to adjust the proposed focus; `⏎` accepts and
  **seeds Monday's plan**. Feels like being *seen*.
- **Empty state:** first week — "not enough history yet; here's what I'll show you
  Friday."
- **Loading:** the narrative streams paragraph by paragraph (a note being written to
  you).
- **AI behavior:** generates the retro with evidence + confidence; proposes forward
  focus; never scolds — honest and warm (personality).
- **Keyboard:** `R` open review · `⏎` accept & seed · `E` edit.
- **Animation:** on "accept & seed," the focus items visibly **travel to next week's
  plan** (causality across time).
- **Why better:** no other tool *generates* the retrospective — Jira makes you build a
  report, Notion makes you write the doc, Sunsama shows raw logs. **Nova reflects for
  you and turns reflection into next week's plan**, closing the loop.
- **Challenge / rejected:** a stats page of charts (that's analytics, not reflection);
  a manual journal prompt (work you have to do).

## 9. Settings — the Trust Console

- **Purpose:** control **how much Nova does on its own**, plus connections and
  behavior — without a preferences maze.
- **Primary action:** **Tune the trust dial.**
- **Information hierarchy:** ① the trust dial (per-capability autonomy) → ②
  connections (Calendar, Finance, GitHub) → ③ working hours & capacity → ④ quiet
  hours → ⑤ appearance.
- **Layout:** the trust dial is the hero; everything else is a short, calm list.

```
   How much should I do on my own?
   ────────────────────────────────────────────────────────────
   Plan my day        Suggest ─●── Auto-draft ──── Auto-run
   File my captures   Suggest ──── Auto-draft ──●─ Auto-run
   Client updates     Suggest ●─── Auto-draft ──── Auto-run
   Reminders          Suggest ──── Auto-draft ──── Auto-run ●

   Connections   Calendar ✓ · Finance ✓ · GitHub +
   Working hours 9–18 · Quiet during focus ✓ · Theme  Dark
```

- **Interactions:** drag each capability along **Suggest → Auto-draft → Auto-run**
  (the progressive-autonomy dial from the vision). Everything is reversible; changes
  take effect immediately with a one-line explanation of what will now happen.
- **Empty state:** new users arrive at **Suggest** on everything (safe default), with
  a note: "I'll ask before doing anything; move a slider right when you trust me."
- **Loading:** instant; connection toggles show live status.
- **AI behavior:** Settings is where the human sets policy and Nova *obeys*; Nova may
  *suggest* moving a slider ("you've accepted 20 morning plans in a row — let me
  auto-run them?") but never moves it itself.
- **Keyboard:** `⌘,` open settings; `Tab` between capabilities; `←/→` adjust a dial.
- **Animation:** the dial thumb springs; a one-line consequence fades in under the
  slider you moved (immediate causality).
- **Why better:** every other tool buries automation in a 200-row preferences table.
  **Nova's settings are a trust console** — the single most important control (how
  autonomous Nova is) is the hero, legible in one glance.
- **Challenge / rejected:** a sprawling tabbed preferences pane (Principle 5); on/off
  automation toggles (too binary — trust is a gradient).

---

# PART V — AI Interaction Patterns (cross-cutting library)

These patterns appear on *every* screen and must be identical everywhere
(Principle 11).

- **The "why" chip.** Any Nova recommendation carries a `why ⌄` that expands inline
  into: the reasons (ranked), the inputs used, and a **confidence** ("high /
  roughly / unsure"). Never a modal, never a separate page. This is Principle 6 made
  concrete.
- **The proposal-review pattern.** When Nova suggests a change (a plan, a structure, a
  rebalance), it's shown as an **editable proposal with Accept / Adjust**, never
  applied silently (unless that capability is set to Auto-run). Adjust opens the
  proposal pre-filled (Principle 7).
- **The change-trace.** When Nova acts (re-plans, files a capture), it leaves a **one-
  line trace** in-context ("moved Moniqo review — over capacity"), quietly, so you can
  always see what it did and undo it (`⌘Z`).
- **The briefing.** The morning surface: top of Today, spoken on voice wake. Batched
  thoughts, calm, ≤5 items. The primary channel for everything non-urgent
  (Principle 8).
- **The interrupt.** Reserved for time-critical / user-requested / trusted-auto only.
  Appears as a single calm banner, never a stack of toasts. Silent during Focus.
- **Confidence & humility.** Nova says "I think," "roughly," "I'm not sure — want me
  to check?" Uncertainty is shown, never hidden (personality + Principle 6).
- **Voice.** Everything above works by voice: `⎵`-hold or "Hey Nova." Voice answers
  are concise; the visual surface mirrors what was said.

---

# PART VI — Global Keyboard Map

| Key | Action | Scope |
|---|---|---|
| `⌘1…⌘7` | Switch lens (Today, Work, Goals, Clients, Finance, Founder, Review) | Global |
| `⌘K` | Command palette (do · go · ask) | Global |
| `⌘N` | Capture | Global |
| `⎵` (hold) | Talk to Nova | Global |
| `⏎` | Primary action of the current screen | Per-screen |
| `J / K` | Move selection down / up | Lists |
| `C` | Capture from context | Most screens |
| `P` | Plan (today/tomorrow) | Today, Planning |
| `R` | Review | Today, Review |
| `?` | Explain (the "why" for the focused item) | Global |
| `U` | Draft update (project/client) | Project, Client |
| `S` | Reveal structure | Project |
| `⌘Z` | Undo Nova's last action / last capture | Global |
| `⌘,` | Settings (trust console) | Global |
| `⌘\` | Collapse sidebar | Global |
| `Esc` | Dismiss / back one level | Global |

**Discipline:** `⏎` is *always* the screen's one primary action (Principle 1), and
`?` is *always* "explain" (Principle 6). Learn two keys, use every screen.

---

# PART VII — Principle Compliance Matrix (the coherence guarantee)

Every screen audited against the locked principles. **No new screen ships without a
row here that passes.** This is how Nova stays one product as it grows.

| Screen | P1 one action | P2 "what next" | P3 ≤7 / calm | P6 explains | P7 corrects | P9 empty teaches | Passes |
|---|---|---|---|---|---|---|---|
| Today | Start top thing | Yes (the now) | 3–5 blocks | why chips | plan pre-made | "shape your day" | ✅ |
| Palette | Run top intent | Yes (ranked) | one list | ask+why | recent verbs | suggested cmds | ✅ |
| Capture | Capture | Yes (files it) | one line | parse chips | pre-filled fix | ghost example | ✅ |
| Planning | Commit plan | Yes (the plan) | timeline | per-block why | proposed plan | drafts from queue | ✅ |
| Project | Do next | Yes (next/blocker) | brief, not board | health why | proposed structure | "how I'd break it down" | ✅ |
| Client | Draft update / next | Yes | brief | ROI why | drafted update | proposed engagement | ✅ |
| Goal | Protect/adjust | Yes (fix drift) | pace line | why-behind | proposed KRs | "what outcome?" | ✅ |
| Founder | Act on lever | Yes (verdict+lever) | verdict + rows | per-row why | drafted rebalance | shows the shape | ✅ |
| Review | Accept & seed | Yes (next focus) | one narrative | evidence | editable focus | "not enough yet" | ✅ |
| Settings | Tune trust dial | Yes (what changes) | dial + short list | consequence line | safe defaults | "move when you trust me" | ✅ |

---

# Closing — and a note on your strategic recommendation

**You're right, and I endorse the pivot.** With this specification, the design stack
is complete:

✅ Product vision · ✅ Architecture · ✅ Data model · ✅ Entity model · ✅ Product
experience · ✅ **UI/UX specification** — and the only remaining design artifact
worth producing before code is **Figma-quality mockups**, which are a *visual
translation* of this document, not new thinking.

Beyond that, more documents will produce less value than a running Nova. The unknowns
that remain — exact motion timings, the real feel of the capture parse, whether the
Founder verdict lands — **can only be discovered by living inside Nova every day.**
The fastest path to a Nova you can't imagine working without is now to **build the
spine (Today · Capture · Project · Planning) and use it**, then let real friction — not
more theory — drive the next decisions.

This document is the canonical UI/UX reference. Every future screen is measured
against Part I and must earn its row in Part VII.

**When you're ready, I can produce the Figma-quality mockups of the four spine
screens (Today, Capture, Project, Planning) as the visual bridge into
implementation — or we start building.**
