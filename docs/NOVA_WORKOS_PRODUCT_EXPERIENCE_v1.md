# Nova WorkOS — Product Experience Vision v1

**Status:** Product & experience design. No implementation, no schemas, no
architecture. The entity model (Objective / Type / Facet, recursive, AI-first) is
frozen and referenced only where it explains *why* an experience is possible.
**Voice:** Head of Product & UX. This is what Nova should *feel* like — the
workflows, the journeys, the delight, and the opinions we're willing to defend.
**The bar:** if OpenAI, Apple, Anthropic, and Linear designed a personal operating
system together, this is the product they'd ship.

---

## 0. The product truth

> **Nova is not an app you maintain. It's a chief of staff you talk to — one that
> sees your entire work and life, tells you what matters right now, and handles the
> organizing so you never have to.**

Every productivity tool ever built asks the user to be a *librarian first and a
doer second*: create the project, pick the folder, set the priority, drag the card,
update the status, write the report. **Nova deletes the librarian.** You capture and
you decide; Nova does everything in between.

The feeling we are chasing, in three words: **calm, certainty, momentum.**
- **Calm** — you open Nova and your shoulders drop, because it's handled.
- **Certainty** — you always know the single most important thing, and *why*.
- **Momentum** — the system moves work forward even when you don't touch it.

---

## 1. The design principles (our opinions, and what they reject)

Each principle is a stake in the ground *against* an entrenched productivity habit.

1. **Capture is a sentence, not a form.**
   *Rejects:* the "New Task" modal with 9 fields. You speak or type one natural
   sentence; Nova extracts the rest. The user never fills a form.

2. **There is no "organize" step. Ever.**
   *Rejects:* folders, tags, moving cards between columns, reparenting, filing.
   Organizing is the tool's job, done by AI, invisibly. The user's only verbs are
   **capture, decide, do.**

3. **One surface answers "what now?"**
   *Rejects:* the home-screen-as-wall-of-boards. Nova's home is a *decision*, not a
   *database*. It shows the answer, not the inventory.

4. **Nova proposes; you approve. Autonomy is a dial you turn, not a default.**
   *Rejects:* both the dumb tool (does nothing) and the scary agent (does things
   behind your back). Nova starts by *suggesting everything*; as you accept, you let
   it *act automatically* on classes of decisions you trust. Trust is earned, never
   assumed.

5. **Every answer carries its "why," one tap away.**
   *Rejects:* black-box priority scores and mystery-meat AI. "Why is this #1?" always
   has a real, human-readable answer. And Nova says "I'm not sure" out loud when it
   isn't.

6. **Structure is revealed, not required.**
   *Rejects:* the mandatory hierarchy. The rich structure (products, projects,
   sub-work) is *there* when you want to see it, and *invisible* when you don't. You
   can work for a month having created nothing but captures.

7. **Silence is a feature.**
   *Rejects:* notification spam, red badges, gamified streak-guilt. Nova is quiet by
   default and speaks only when it has earned the interruption. A calm tool is a
   trusted tool.

---

## 2. How you interact with Nova

Two modes, always available, never in conflict:

- **Tell Nova** (conversation) — the primary input. A single, omnipresent line
  (keyboard shortcut anywhere; voice on wake). You talk to Nova the way you'd talk to
  a sharp EA: *"push the Acme export to Monday," "how's Moniqo doing?," "block two
  hours for deep work tomorrow morning."* No syntax, no commands to memorize.
- **Show me** (glance) — the visual layer. Calm, spatial, glanceable surfaces
  (Today, a project, a goal, the founder view). You *read* these; you rarely *edit*
  them, because editing happens by conversation.

**Voice-first, not voice-only.** You can run your whole morning by talking while
making coffee, or work silently by keyboard. Both are first-class. Nothing is
buried in a menu that voice can't reach, and nothing requires voice.

**The trust dial (progressive autonomy).** Every class of Nova's help has three
settings the user controls: **Suggest** (Nova proposes, you approve each time) →
**Auto-draft** (Nova prepares it silently, you review a batch) → **Auto-run** (Nova
just does it and tells you). New users start at *Suggest* on everything. Over weeks,
as they keep accepting Nova's morning plans, they flip "plan my mornings" to
*Auto-run*. This is the Apple-meets-Anthropic posture: powerful, but never
surprising, always reversible, always the user's choice.

---

## 3. The thirteen questions, answered as design

### 3.1 — The first time you open Nova (onboarding)

**There is no empty state. There is no "create your first project" wizard.** Those
are the original sin of every productivity app — they hand you a blank canvas and a
chore.

Instead, Nova opens with a warm, quiet screen and one line: *"Tell me what you're
working on right now — just talk, I'll organize it."* You brain-dump, by voice or
text, for two or three minutes:

> *"I'm building Nova, my personal OS. I've got SplitEasy which is live and needs a
> bug-fix release, Moniqo is early, DigiHealth is just an idea. I freelance for Acme
> — owe them an analytics dashboard by the 25th, worth two lakh. And I want to
> actually learn Rust this quarter."*

And then the **first magic moment**: as you speak, Nova *builds your world in front
of you*. Products appear. The Acme engagement forms with its deadline and value. A
Rust learning goal takes shape. The DigiHealth idea files itself as a spark to
revisit. You didn't create anything — **you described your life and it became
organized.** You end onboarding by *watching your own portfolio assemble itself*,
not by staring at a blank board.

Then Nova offers — never forces — to connect Calendar, Finance (already yours), and
GitHub, framed as *"want me to see your calendar so I can plan realistically?"* And
it closes with the thing that hooks: **your first briefing.** *"Here's what I'd focus
on tomorrow, and why."* Ninety seconds in, Nova has already been useful.

### 3.2 — The home screen: "Today"

Not a dashboard. Not a board. **A single, calm answer to "what should I do right
now, and why?"** It reads like a morning note from a chief of staff:

- **The one thing.** At the very top, one sentence: *"Start with the Acme export —
  it's due Friday, worth ₹40k, and it's blocking their sign-off."* This is the whole
  product in one line.
- **Today's shape.** Three to five time-blocks Nova has already planned around your
  calendar, each with a one-line reason. Not a to-do list of 40 things — the *few*
  that fit today.
- **On your mind.** A thin strip: one approaching deadline, one risk, one gentle
  nudge (*"you haven't touched Rust in two weeks"*). Enough awareness, never anxiety.

Everything else — projects, goals, freelancing, finance — is one tap or one sentence
away, but the home never shoves the whole database at you. **The home is a decision,
not an inventory.** You should be able to look at it for five seconds and know
exactly what to do.

### 3.3 — Capturing an idea

The single most-used gesture, and it must be **frictionless to the point of
invisible.** One shortcut from anywhere (or "Hey Nova"), one line, natural language:

> *"Build CSV export for Acme, about 4 hours, due Friday, worth 40k."*

Nova understands: this is work, for Acme, due Friday (a hard deadline), ~4h, ₹40k of
value — and **files it under the Acme engagement, in the right place, decorated with
all of that**, in under two seconds. It shows a tiny, glanceable confirmation of what
it understood — *"Task · Acme · Fri · 4h · ₹40k"* — with one tap to fix anything.

You never pick a project. You never choose a type. You never set a priority. You
**dump the thought and it lands perfectly placed.** A messy 2am voice note — *"ugh
don't forget the split logic breaks on 3-way in SplitEasy"* — becomes a bug filed
under SplitEasy's release, ready for triage. **Capture → placed → decorated. Zero
organizing, every time.**

### 3.4 — Planning your day

You do **not** drag cards onto a calendar. That's construction work, and it's Nova's
job. When you sit down, **the day is already drafted** — time-blocked, capacity-aware,
merged with your real calendar, sequenced to your energy (deep work when you're
sharp), each block carrying a one-line *why*.

Your role is a thirty-second **review, not a build**:
- Glance. Nod.
- Or nudge by voice: *"move the deep work to the morning, I have energy then,"* or
  *"I don't have the head for the hard stuff today — give me lighter wins."* Nova
  re-flows instantly.
- One tap to commit.

And then the part that makes it feel alive: **the plan adapts to reality without you
asking.** A meeting runs 40 minutes over? By the time you're out, Nova has already
re-flowed your afternoon and left you a one-line note: *"Bumped the Moniqo review to
tomorrow; kept the Acme block — it's the deadline."* Planning stops being a morning
chore and becomes a *continuous, invisible service.*

### 3.5 — How projects should feel

A project is **not a board you tend.** It's a living thing with a heartbeat you can
check. Open one and you get, in plain language:

- **A status you didn't write.** *"On track. Auth is done; the export page is the
  critical path, roughly two weeks out. One risk: waiting on Acme's API keys."*
- **The few things that matter** — next actions, the one blocker, the health.
- **The money and the time** — expected vs realized revenue, hours invested, and
  what that means (ROI), woven right in (§3.8).

The full structure — sub-work, dependencies, the tree — is *there* if you want to
drill in (and because the underlying model is one fluid recursive structure, drilling
in and reorganizing never breaks anything). But the **default is the narrative**, not
the columns. Projects feel like *reading a crisp status report that wrote itself.*

### 3.6 — How goals should feel

Goals are **not a quarterly ceremony you update and forget.** They're **always-on
gravity.** A goal shows its *trajectory* — not just "40% done" but *"are you actually
moving, at the rate you need?"* — what's contributing to it, and the honest truth
when you've drifted.

The magic is the connection Nova draws *for* you: *"Acme is your top revenue
contributor to your ₹10L goal this quarter,"* or the harder one — *"You said learning
Rust mattered this quarter. You've logged zero hours in three weeks. Want me to
protect two hours on Thursdays?"* Goals feel like **a compass that's always pointing,
and a friend willing to tell you when you've stopped walking toward them.**

### 3.7 — How freelancing should feel

Freelancing is a **first-class stream of your life, not a "project" in a list.** Each
client feels like a lightweight fusion of CRM + delivery + money:

- What you owe them, by when, and what it's worth.
- Expected vs realized revenue, and **ROI-per-hour** — the number freelancers never
  compute and desperately need.
- The relationship context — last contact, what's outstanding.

And Nova acts like an **account manager for your own client work**: it drafts the
weekly client update *from your actual activity* (§3.13), warns you before a
deliverable slips, and — the truth you need — tells you *which client is actually
worth your time*: *"Acme is ₹2,200/hr realized; the Beta client is ₹600/hr and eating
your best mornings."* Freelancing stops feeling like scattered obligations and starts
feeling like a **managed book of business.**

### 3.8 — How finance integrates naturally

Finance is already built — and it should **almost never be a place you visit.** Money
shows up **where it changes a decision**, woven into work:

- A project shows expected vs realized revenue inline.
- The priority queue *weighs* revenue (the ₹40k task ranks above the ₹0 refactor,
  and Nova says so).
- The founder view shows ROI-per-hour across your whole portfolio.
- And Nova narrates the fusion: *"Acme paid the ₹40k invoice — that project just went
  net positive at ₹2,200/hour,"* or the uncomfortable one, *"You've put 60 hours into
  Moniqo for ₹0 so far. Intentional, or should it drop down the queue?"*

Work and money become **one honest story**, not two tabs you reconcile in your head.
The Finance section still exists for when you want the ledger — but the *experience*
is that money quietly informs every work decision, exactly when it's relevant.

### 3.9 — When the AI should interrupt you

This is where most tools destroy trust. Nova's rule is strict:

> **Interrupt only when the cost of waiting exceeds the cost of the interruption.**

By default, Nova is **quiet.** It batches its thoughts into two calm touchpoints: the
**morning briefing** and an optional **evening reflection.** Everything non-urgent
waits for one of those.

Nova breaks silence *in the moment* for exactly three reasons:
1. **A real, time-sensitive risk** — a hard deadline about to slip, a meeting
   starting in five minutes, a commitment that will be missed today.
2. **Something you explicitly asked it to watch** — *"tell me the second Acme
   replies."*
3. **A quick confirm to act on a standing instruction** — *"the invoice cleared;
   okay to mark the project net-positive?"* (and once you trust it, even this goes
   silent).

**During a focus session, Nova goes fully dark** except for a genuine emergency. It
would rather miss a minor nudge than break your flow. A tool that respects your
attention is a tool you'll keep for ten years.

### 3.10 / 3.11 / 3.12 — The Zero-Organization Doctrine

These three questions are one philosophy: **the user does the thinking; Nova does the
bookkeeping.**

**What should NEVER require manual work (Q10):**
Filing. Tagging. Choosing a project. Picking a type. Moving cards between columns.
Setting priority numbers. Linking related items. Rolling up status to parents.
Writing status reports. Maintaining a roadmap. Categorizing captures. Scheduling into
the calendar. Re-planning when something slips. *If Nova can infer it, the user never
touches it.* The user only ever **corrects**, never **constructs.**

**What should be AUTOMATIC (Q11):**
Prioritization. Day-planning. Status roll-ups. Project health. Deadline-risk
detection. Revenue attribution and ROI. Estimate calibration (Nova learns your
personal "×1.6 on backend tasks"). Dependency detection. Turning meeting notes into
action items. Briefings and reviews. Reminders. Re-planning against reality.
Connecting daily work to goals. Surfacing what's gone stale. **All of it automatic,
all of it explainable, all of it reversible.**

**What the user should NEVER think about (Q12):**
Where something "goes." The hierarchy. What's most important (Nova ranks it). Whether
they're forgetting something (Nova remembers everything). How long something will take
(Nova estimates from history). Whether a deadline is at risk (Nova watches). The tool
itself. **The user thinks about their work and their life — never about the system
that holds them.**

### 3.13 — The magical moments

The moments that make someone say *"I can't imagine working without Nova."* Each is a
concrete, shippable experience:

1. **The three-minute life-organizer.** You talk for three minutes on day one and
   watch your entire portfolio — products, clients, goals — assemble itself. You never
   face a blank canvas.
2. **The morning that plans itself.** You wake up and the day is already optimally
   planned, with reasons. You just say *"yes."*
3. **The capture that files itself.** You dump a messy thought and it lands perfectly
   placed and decorated. You realize you'll never file anything again.
4. **The re-plan that just happens.** A meeting runs long; by the time you're out,
   your afternoon has already re-flowed, and Nova tells you what moved and why.
5. **The status report you didn't write.** A client asks *"how's it going?"* and Nova
   has already drafted the update from your real work — you just hit send.
6. **The truth you needed to hear.** *"You've spent 62% of your hours on your
   lowest-ROI project — and it's not the one you said mattered most."* The AI as an
   honest chief of staff, not a cheerleader.
7. **The thing you forgot, remembered for you.** *"You promised Moniqo's beta by
   Friday three weeks ago and haven't touched it. Still real, or should I let it go?"*
   Nothing falls through the cracks, ever again.
8. **The week that reflects itself.** Friday evening, a review appears — what you
   shipped, where your hours actually went, what's at risk next week — and it quietly
   seeds Monday. You feel *understood by your own system.*
9. **One queue for a whole life.** A client deadline, a learning goal, and a health
   habit ranked honestly in a single list — because Nova is the only thing that sees
   *all* of you. No other tool even attempts this.

The through-line: **Nova gives you back the thing every other tool takes — your
attention — and hands you certainty in return.**

---

## 4. Nova's personality

The way Nova speaks is part of the product. It is:

- **Calm and concise.** Short sentences. No walls of text. It respects that you're
  busy.
- **Honest, including when it's uncomfortable.** It will tell you the ROI truth, the
  drifted goal, the neglected promise. A chief of staff who only flatters is useless.
- **Humble about uncertainty.** It says *"I think,"* *"roughly,"* *"I'm not sure —
  want me to check?"* It never fakes confidence it doesn't have.
- **Warm, never chirpy.** No exclamation-mark confetti, no gamified guilt, no
  "You're on a 12-day streak! 🔥" manipulation. Encouraging like a good colleague,
  not a slot machine.
- **Deferential on decisions, decisive on preparation.** It does the analysis and
  the drafting; it leaves the *choosing* to you.

The blend: **Anthropic's honesty, Apple's calm, OpenAI's fluency, Linear's speed.**

---

## 5. What we deliberately reject

Naming the enemy keeps us honest. Nova is **not**:

- **A wall of boards as a home.** (Kanban is a *view*, never the front door.)
- **An infinite backlog that induces dread.** (Nova shows you *today's few*, and
  holds the rest silently.)
- **A manual prioritization exercise.** (You never drag to reorder a list of 200.)
- **A notification firehose.** (Silence by default; earned interruptions only.)
- **A gamified streak-guilt machine.** (Motivation through honesty, not dopamine
  tricks.)
- **An empty canvas demanding setup.** (You describe your life; it organizes.)
- **A place where "projects" are mandatory bureaucracy.** (Structure is optional and
  invisible until useful.)
- **A tool that needs a weekly "grooming" ritual to stay useful.** (It grooms
  itself.)

If a feature makes Nova feel more like Jira, Notion, ClickUp, or Asana, it is wrong,
no matter how "powerful" it is.

---

## 6. A day in the life (the whole vision, end to end)

> **7:10 am.** You pour coffee and say, *"Morning, Nova."* It reads you the briefing:
> *"Two things matter today. Start with the Acme export — due Friday, ₹40k, blocking
> their sign-off. Then the SplitEasy 3-way split bug; it's small and it's been open a
> week. I've protected your morning for deep work and pushed the Moniqo review to
> tomorrow — you were over capacity. One nudge: still zero hours on Rust this week."*
> You say, *"Yep, and block Thursday morning for Rust."* Done.
>
> **9:00 am.** You start the Acme block. Nova is silent — you're in focus.
>
> **11:40 am.** A call runs 40 minutes over. You come out to a single calm note:
> *"Re-flowed your afternoon. Kept the SplitEasy fix; moved the DigiHealth spike to
> Friday."*
>
> **2:15 pm.** A thought hits: *"Nova — the export needs pagination, maybe 2 hours."*
> It's captured, placed under Acme, estimated, gone from your head.
>
> **4:30 pm.** Acme emails: *"How's it looking?"* You ask Nova; it has already drafted
> the update from today's work. You read it, tweak one line, send.
>
> **6:00 pm.** Evening reflection, optional, thirty seconds: *"You shipped the export
> and the SplitEasy fix. Acme's now 70% delivered, tracking for Friday. Tomorrow's
> already planned. Nice day."*
>
> You never opened a board. You never filed a task. You never wrote a status report.
> You never wondered what to do next. **You just worked — and Nova held everything
> else.**

---

## 7. The north star

Every roadmap decision, every screen, every word Nova speaks should be measured
against one test:

> **Does this make the user do *less* organizing and feel *more* certain about what
> matters?**

If yes, it's Nova. If it adds a field, a folder, a step, or a moment of "where does
this go?" — it isn't, no matter how capable it sounds.

We are not building a better project manager. **We are building the first system that
runs a founder's whole life *with* them — so they can stop managing their work and
start doing it.** That is the product that makes someone say, and mean:

> *"I can't imagine working without Nova."*
