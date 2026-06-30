# Rai — Roadmap, Chapter 2

The original roadmap (Phases 0–5) is done: Rai listens, remembers, thinks, runs
in the background, and gives a proactive briefing. This file is the next chapter —
turning Rai from a command-runner into something that feels like a personal
assistant that understands you.

Same rules as before: **build one phase at a time, in order, and stop after each
so it can be tested before the next.** This file lists a lot of features on
purpose. It is a menu, not a mandate — not every phase has to be built, and none
should be rushed. Depth beats breadth.

---

## How to use this file (instructions for Claude Code)

- Build phases **in dependency order**, top to bottom. Later phases assume
  earlier ones exist.
- After each phase, stop and let me test against its "Done when" list before
  continuing. Never merge multiple phases into one pass.
- Keep secrets in `.env` (already set up), never hardcoded. `.env` stays in
  `.gitignore`.
- macOS will prompt for new permissions (Calendar, etc.) the first time — that's
  expected; don't try to suppress it.
- Don't add scope that isn't written here without asking first.

## The keystone: Phase 12 makes everything else sustainable

Read this before building anything. Right now routing is hand-coded
(`memory → launcher → Claude`) with brittle keyword matching — which is why
"how many profiles in my chrome" once opened Chrome. As features grow, that
hand-coded routing gets worse. **Phase 12 (smart intent routing) is the fix that
makes a large feature set maintainable.** You can build Phases 7–11 first on the
current routing, but the moment it feels tangled, jump to Phase 12 — it pays for
itself.

---

## Phase 7 — Calendar & due dates  ·  START HERE

**Objective:** Rai reads and writes your real macOS Calendar, and reminders/tasks
have working dates.

**Approach:** Drive the native macOS Calendar via `osascript` (AppleScript) for
creating events — simplest, no OAuth. For reading events, use `osascript` or
EventKit via PyObjC if AppleScript reads prove unreliable. No Google account
needed. Google Calendar sync is explicitly deferred (see "Later" at the bottom).

**Build:**
- `add_calendar_event(title, date, time)` → creates an event in the default
  macOS calendar via `osascript`.
- `get_events(day)` → returns events for today / a given day.
- Wire the existing `tasks.due` field: "add task X due Friday" parses the date
  and stores it.
- A `reminders` table `(id, text, remind_date, created_at)` plus a handler for
  "remind me that &lt;text&gt; on &lt;date&gt;".
- Natural date parsing ("tomorrow", "next Friday", "31st July") — use a small
  date-parsing helper.
- Voice queries: "what's on my calendar today / tomorrow?"

**Done when:**
- "Rai, add a calendar event: dentist on July 10 at 4pm" creates a real event you
  can see in Calendar.app.
- "What's on my calendar tomorrow?" reads back real events.
- "Remind me that 31 July is dad's birthday" saves a dated reminder.

**Constraints:** native macOS Calendar only this phase. No cloud calendar.

---

## Phase 8 — Proactive intelligence  ·  builds on Phase 5 + 7

**Objective:** Rai surfaces the right things at the right time, unprompted.

**Build:**
- Enrich the morning briefing: today's calendar events + reminders due today +
  top open tasks + a one-line money summary (in rupees).
- **Reminders actually fire:** the daily check surfaces any reminder whose
  `remind_date` is today (so dad's birthday is spoken on the 31st, not just
  stored).
- Optional evening wrap-up: what got done, what's open, tomorrow's first event.
- Time-aware nudge (optional): if an event is within 30 minutes, Rai can announce
  it. Keep this off by default until tested — it needs the daemon checking on a
  timer.

**Done when:** on a day with a due reminder, the morning briefing speaks it
without being asked.

**Constraints:** keep briefings short and spoken-friendly. One or two sentences,
not a monologue.

---

## Phase 9 — The learning loop  ·  the "understand me" phase

**Objective:** Rai builds an evolving picture of you and reasons over it, instead
of only storing transactions. This is what makes it feel like it learns.

**Build:**
- A `profile` table `(id, observation, category, confidence, updated_at)` — holds
  *observations* about you ("works best in mornings", "prefers Hinglish",
  "hasn't touched Moniqo in 2 weeks"), distinct from the fact tables.
- A **reflection job**: on a weekly schedule (run by the daemon), feed recent
  logs (tasks, money, progress, completed vs missed) to Claude and ask it to
  extract patterns and write them back as concise profile observations. Dedupe /
  update existing observations rather than piling up duplicates.
- Feed the profile into `_build_prompt()` so every reply is personalized.

**Done when:** after a couple of weeks of use, asking "how am I doing?" gives an
answer grounded in observed patterns, not generic advice.

**Honest note for the builder:** this needs accumulated real usage before it says
anything insightful. Build the machinery now; the "it gets me" quality emerges
over weeks. It reflects the user's own data back at them intelligently — a sharp
mirror, not a mind that knows them.

---

## Phase 10 — Conversational depth  ·  the "1-on-1 with me" wish

**Objective:** Rai holds a real conversation, not just one-shot Q&A.

**Build:**
- Pass recent conversation history into each Claude call so follow-ups have
  context (within the existing conversation-mode window, and optionally a short
  rolling session memory).
- Reflective conversations: "how was my week?", "talk me through my goals" —
  Rai uses the profile + logs to have an actual back-and-forth.
- Rai asks clarifying questions when a request is ambiguous, instead of guessing.
- Optional journaling mode: "Rai, journal — ..." logs a reflective entry into
  `progress` and Rai responds thoughtfully.

**Done when:** you can have a 4–5 turn spoken conversation where Rai remembers
what was said earlier in the same exchange.

**Constraints:** keep token cost in check — send a trimmed history, not the whole
transcript. Use the cheap model for routine turns.

---

## Phase 11 — Read-only external integrations  ·  "what's new"

**Objective:** Rai checks sources that *want* to be read programmatically and
summarizes what's new. Each source is its own small build with its own auth.

**Build (one source at a time, easiest first):**
- **Weather** — "what's the weather?" (simple public API, no auth).
- **GitHub** — new issues / PRs / notifications (you already use it; clean token
  auth).
- **Gmail** — unread / important summary (Gmail API, OAuth).
- **RSS / news** — updates from sites that publish feeds.

**Explicitly excluded:** sites that prohibit automated reading and have no
personal API — e.g. LinkedIn, Instagram feeds. Do not build feed-scraping against
these; it risks the account and breaks their terms. If asked, Rai should say it
can't read that source rather than attempt a scrape.

**Done when:** "anything new on GitHub?" returns a real spoken summary.

**Constraints:** read-only. No posting, sending, or deleting on the user's behalf
without explicit per-action confirmation.

---

## Phase 12 — Smart intent routing  ·  the keystone

**Objective:** Replace brittle keyword matching with Claude deciding what the user
wants and which Rai function to run.

**Build:**
- Give Claude a list of Rai's capabilities as callable tools/functions (open app,
  add task, add reminder, add calendar event, log money, query money, get events,
  etc.).
- On each request, Claude classifies intent and either answers or returns which
  function to call with what arguments; Rai executes it.
- This removes the verb-gate hack and the "mentions chrome → opens chrome" class
  of bugs permanently, and makes adding future features trivial — you add a
  function, not another keyword rule.

**Done when:** "how many profiles in my chrome" answers the question, while "open
chrome" opens it — with no hand-coded keyword rules.

**Constraints:** keep a fast local path for the most common commands if latency
matters, but let Claude own ambiguous cases.

---

## Phase 13 — Productivity & life-tracking expansions  ·  the buffet

**Objective:** Breadth. Pick the ones you'll actually use; ignore the rest.

**Candidate features (each small, independent):**
- Habit tracking — log and review daily habits.
- Focus / Pomodoro timer by voice.
- Quick voice notes / memos into `progress`.
- Web search answers (via Claude's search if available).
- Quick math, unit and currency conversion.
- "Read me my day" — full spoken rundown on demand.
- Spending insights — "how much did I spend this week?" with simple breakdowns.

**Done when:** each feature you choose works in isolation and is tested.

**Constraints:** add one at a time. Resist building all of them — an unused
feature is maintenance debt, not value.

---

## Phase 14 — Polish & personalization

**Objective:** Make Rai pleasant to live with.

**Build:**
- Custom voice — local neural TTS (Piper/Kokoro) via the swappable `speak()` /
  `TTS_ENGINE` design, for a far more natural voice than `say`.
- Hindi / Hinglish — multilingual Whisper model + `REPLY_LANGUAGE` + a Hindi TTS
  voice. Bilingual by design.
- A short wake cue (a soft sound or "mm?") when Rai wakes, so you know it's
  listening and stop over-repeating the wake word.
- Graceful error recovery — never dump the user to "use another app"; Rai should
  use a capability it has or say plainly what it can't do.

**Done when:** Rai sounds natural, handles Hinglish, and signals when it's
listening.

---

## Later / explicitly deferred

- **Google Calendar / cloud sync** — only if native macOS Calendar isn't enough.
  Adds OAuth complexity.
- **Cloudflare Worker key proxy** — only needed if Rai's brain ships inside a
  public product. Not for personal use.
- **Automatic money tracking** (bank/UPI sync, receipt OCR) — a separate large
  project; voice/text logging covers most of the value.
- **Sending / posting on your behalf** (email replies, social posts) — out of
  scope for now; read-only is the safe boundary.

---

## One principle to keep the whole thing healthy

The model does not rewrite itself — "learning" here means memory + reflection +
using what's stored, not the AI becoming a different mind. And Rai is a very good
tool for thinking and staying organized; it is not a substitute for people. Build
it to serve you, use it daily, and let the features you actually reach for tell
you which of these phases were worth it.
