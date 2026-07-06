# Rai — Roadmap, Chapter 3: The Visual Layer

Chapters 1 and 2 built Rai's mind: it listens, remembers, thinks, routes intent,
runs in the background, learns, and integrates. This chapter gives it a **face** —
a way to *see* what Rai is doing instead of only hearing it.

The mockups already designed (dashboard, full view, conversation view, reminder
view, floating companion) are the visual targets. This file is the build order.

Same rules: **one phase at a time, in order, test each before the next.**

---

## The two principles that govern this whole chapter

1. **Read-only first, always.** The visual layer starts as a *window* into
   Rai's data — it displays, it does not change anything. This is deliberate:
   the fake-reminder incident (Rai said "saved!" and saved nothing) proved that
   what Rai *says* can't be trusted; a screen that only ever shows what's
   actually in the database *can* be. Displaying is safe. Acting from the UI is a
   later, carefully-gated step (Phase 21).

2. **Show only what's real.** A panel appears only when the data behind it
   actually exists. Never render a "Calendar" or "Learned" panel that would sit
   empty or, worse, show fake content — that repeats the exact lying problem in
   visual form. Panels light up as their underlying capability is confirmed.

---

## Technical decisions (already reasoned through — don't relitigate)

- **The dashboard** is a small local web server (FastAPI + uvicorn) in a
  SEPARATE file (`dashboard.py`) that READS `nova.db`. It never imports or
  modifies `nova.py`. It serves a page at `http://localhost:8000` — local only,
  nothing public, nothing uploaded. Rai's voice daemon and the dashboard run
  side by side against the same database.
- **The floating companion** graduates Rai into a packaged Mac `.app`. Two valid
  paths: **pywebview** (recommended — reuse the mockup HTML as the UI, keep
  everything in one Python process) or **Swift/SwiftUI** (best native feel,
  cleanest permissions, but a new language and bigger time cost). Pick per goal:
  fastest result → pywebview; best-feeling result → Swift.
- **Packaging matters for permissions.** macOS grants mic, notifications, and
  accessibility to an *app*, not a loose script — which is why the companion
  phase is also the "make Rai a real .app" phase.

---

## Phase 15 — Local web dashboard v1 (read-only shell)  ·  START HERE

**Objective:** A local webpage showing Rai's real data, live.

**Build:** `dashboard.py`, FastAPI + uvicorn (add to requirements.txt), serves
one HTML page on localhost:8000. Reads `nova.db` only — never writes.
Panels, using ONLY data that exists today:
- Summary metrics: reminder count, open-todo count, earned and spent this month
  (rupees).
- Upcoming reminders (text + date), soonest first.
- Open todos (text + due if present).
- Live activity feed: most recent ~15 rows across tables, newest first, with
  relative timestamps ("2 min ago"). Derive from `created_at` if there's no
  dedicated events table.
Auto-refresh every ~15s so new voice activity appears without reload. Plain
HTML/CSS, mobile-friendly. Match the dashboard mockup's layout.

**Done when:** visiting localhost:8000 shows your real reminders and a live
activity feed that updates after you speak to Rai.

**Constraints:** read-only. Separate file. Leave commented placeholders for
calendar / insights / money-chart panels (added later). Include run instructions
in a comment.

---

## Phase 16 — Full dashboard view  ·  builds on 15

**Objective:** The complete app window from the "full view" mockup.

**Build:**
- Add a left sidebar nav (Home, Reminders, Todos, Money, Talk, Insights,
  Settings) with Home as the landing view.
- Light up the panels whose data now exists: a **Today** strip from the calendar
  (Chapter 2 Phase 7), a **money breakdown** bar (earned vs spent), and a
  **"What Rai has learned"** panel from the profile table (Chapter 2 Phase 9).
- Each panel still reads live from the DB; still read-only.

**Done when:** the full view renders every section from real data, and empty
sections say so honestly rather than faking content.

**Constraints:** if a Chapter-2 capability wasn't actually built, that panel
stays a placeholder — do not fabricate its contents.

---

## Phase 17 — Reminder view + native notifications

**Objective:** The reminder screen, and reminders that actually *fire* on the
day as real macOS notifications.

**Build:**
- A reminders page: a highlighted "firing today" card at top, an "Upcoming"
  list below (from the reminder mockup).
- Native macOS notification when a reminder is due today (via the daemon's daily
  check + a notification call). This is the piece that makes a reminder a real
  reminder, not just a stored row.

**Done when:** on a day with a due reminder, a real macOS notification appears,
and the reminder view shows it as "today".

**Constraints:** notification firing is a read/notify action, still not UI-driven
writes. Action buttons (snooze/done) come in Phase 21.

---

## Phase 18 — Conversation view  ·  needs Chapter 2 Phase 10

**Objective:** A chat view of the spoken back-and-forth, with actions shown
inline.

**Build:**
- Render the recent conversation (from session memory) as chat bubbles: user
  turns and Rai turns.
- When a turn triggered an action, show the action card INLINE inside Rai's
  reply (e.g. "Saved reminder · …") — the same say-it-and-show-it trust pattern.
- A text input as an alternative to voice.

**Done when:** a spoken exchange appears as a readable conversation with any
actions shown inline as cards.

**Constraints:** depends on session memory existing. If Chapter 2 Phase 10 isn't
built, build it first or defer this phase.

---

## Phase 19 — Package Rai as a Mac app + permissions

**Objective:** Turn `python nova.py` into a real, double-clickable `.app` so
macOS permissions grant cleanly.

**Build:**
- Bundle the Python app (e.g. with `py2app` / `briefcase`, or via the pywebview
  app if going that route).
- Handle the permission grants Rai needs: Microphone (have it), Notifications,
  and Accessibility. Screen Recording ONLY if screen capture is ever added
  (it isn't yet — don't request it).
- App launches the voice daemon + the dashboard server together.

**Done when:** Rai runs as a packaged `.app`, prompts for its permissions once,
and starts listening on launch.

**Constraints:** request only the permissions actually used. No Screen Recording.

---

## Phase 20 — Floating always-on-top companion

**Objective:** The HUD from the floating-companion mockup — a small panel pinned
on top of everything.

**Build (pywebview recommended, reusing the mockup HTML):**
- A small always-on-top window, collapsed to a quiet orb by default.
- Expands on wake word: shows a live audio waveform while listening, echoes the
  transcript, and drops an action card the moment something is saved/done.
- Collapses back after a short idle.
- Stays visible across Spaces / over fullscreen apps (the window-level nuance —
  easier in Qt/Swift, finicky in pywebview; test and accept the tradeoff).

**Done when:** the companion floats over other apps, wakes on "Alex", shows the
waveform + transcript + action card, and collapses when idle.

**Constraints:** the companion READS state and DISPLAYS it. It doesn't introduce
new write paths — the voice loop is still what acts.

---

## Phase 21 — Actionable UI (crosses read-only → doing)  ·  gated

**Objective:** Let the UI *do* things, deliberately and safely.

**Build (one action at a time):**
- Reminder actions: snooze, mark done.
- "Draft a wish" style helpers that generate content for a reminder.
- Any other button that writes to the DB or acts on your behalf.

**Done when:** a chosen UI action writes back correctly with clear visual
confirmation of what happened.

**Constraints — read this:** this is the phase that leaves the safe read-only
boundary. Every write must give unmistakable feedback (the activity feed logs
it, the UI updates). Anything that acts *outside* Rai (sending a message,
posting) requires explicit per-action confirmation — never fire on a single
click without a confirm step. Add these slowly; a UI that quietly does things is
how trust breaks.

---

## Phase 22 — Frontier: contextual visualization  ·  experimental / someday

**Objective:** Rai generates a relevant visual for whatever you're discussing —
a chart because you mentioned revenue, a diagram because you asked about a system.

**Reality check:** this is doing live, on your machine, what a chat assistant
does when it renders a diagram — a genuinely research-level build (intent →
choose a visual type → generate valid render → display). It is NOT v1 and should
not block any earlier phase.

**Sensible first step (if attempted):** limit it to a few fixed chart types over
your own data ("show my spending this month" → a bar chart), not arbitrary
topic visualization. Grow from there only if it earns its keep.

**Done when:** (aspirational) — treat anything here as a bonus experiment.

---

## The order, and the honest weight

Build 15 → 16 → 17 → 18 first: these are all local, read-only, and reuse the web
skills and the finished mockups — genuinely low-risk. Phase 19 (app-ification) is
the real step-change in effort, because packaging + permissions is fiddlier than
any single feature. Phases 20–21 are where Rai becomes an ambient, acting
presence — powerful, and the point where care matters most. Phase 22 is a
someday.

The recurring rule across all of it: **the screen must never claim more than the
database contains.** A visual that shows only what's real is Rai's honesty made
visible — which is the whole reason to build it.
