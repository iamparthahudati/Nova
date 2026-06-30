# Rai — Build Roadmap

A local-first, voice-controlled personal assistant for macOS that grows into a
proactive PA and product-pipeline tracker. This file is the build spec. Work
**one phase at a time, top to bottom.** Do not start a phase until the previous
phase's "Done when" criteria are met.

---

## How to use this file (instructions for Claude Code)

- Build phases **in order**. Each phase depends on the one before it.
- After finishing a phase, stop and let me test it against its "Done when" list
  before starting the next.
- **Keep everything minimal.** Single file (`rai.py`) until a phase explicitly
  says otherwise. No threading, config frameworks, extra features, or
  dependencies beyond what each phase lists.
- Never hardcode secrets. Read keys from environment variables.
- If you think a phase needs something not written here, ask first — don't add
  scope on your own.

---

## Stack and requirements (whole project)

Already available on the machine:
- macOS + a working Python 3.9+ environment
- Cursor / Claude Code
- A Claude API key, reachable via an existing Cloudflare Worker proxy

Install as needed (all free, no accounts):
- `portaudio` — `brew install portaudio` (run before pip installs)
- `faster-whisper` — local speech-to-text, no key, no account
- `sounddevice`, `numpy` — mic recording
- `sqlite3` — ships with Python, nothing to install
- `python-dotenv` — loads `.env` secrets at startup
- macOS `say` — built in, nothing to install

The **only credential** in the entire project is the Claude API key, and it is
not used until Phase 3.

Permissions: grant microphone access to the terminal/Cursor on first run.

---

## Phase 0 — Keyword launcher  ·  STATUS: DONE

The existing `rai.py`: press Enter, record ~4s with `sounddevice`, transcribe
with `faster-whisper`, substring-match against a `COMMANDS` dict, launch the app
or URL with `subprocess`. This is the foundation every later phase builds on.
Keep its `COMMANDS` dict and the `transcribe()`, `match_command()`,
`run_command()` functions intact through all later phases unless told otherwise.

---

## Phase 1 — Always-on voice  ·  ~3–4 hrs

**Objective:** Remove the Enter key. Rai listens continuously, wakes on the word
"rai", runs the existing command pipeline, and speaks a short confirmation.

**Dependencies:** none new. Wake word is done with `faster-whisper` only (no
Porcupine, no openWakeWord, no accounts).

**Files:** modify `rai.py` only.

**Config variables (top of file):**
- `WAKE_WORD = "rai"`
- `CHUNK_SECONDS = 2`
- `HOP_SECONDS = 1` (overlap so the word isn't missed across a boundary)
- `RMS_THRESHOLD = 0.01` (below this volume, treat as silence and skip Whisper)
- `COMMAND_RECORD_SECONDS = 4`

**Behavior:**
1. On startup print "Rai is listening for the wake word...".
2. Continuously record `CHUNK_SECONDS` of 16kHz mono audio, advancing by
   `HOP_SECONDS` each loop (overlapping windows).
3. For each chunk compute RMS amplitude with numpy. **If below `RMS_THRESHOLD`,
   skip transcription entirely** — `faster-whisper` hallucinates text on silence
   (returns things like "you" or "Thank you."), so the volume gate prevents
   false triggers and saves CPU. Add a comment explaining this.
4. Otherwise transcribe the chunk, lowercase it, check if `WAKE_WORD` is a
   substring.
5. On detection: print "Wake word detected!", then call the existing pipeline —
   record `COMMAND_RECORD_SECONDS`, `transcribe()`, `match_command()`,
   `run_command()` — exactly as the old Enter path did.
6. After handling a command, speak a one-line confirmation via macOS `say`
   (e.g. `subprocess.run(["say", "Opening Chrome"])`), then resume listening.
7. Ctrl+C exits cleanly and releases the mic.

**Done when:**
- "Rai, open Chrome" works fully hands-free.
- Rai speaks a confirmation after acting.
- It does not fire on silence or background noise (tune `RMS_THRESHOLD`).

**Constraints:** single file, terminal stays visible (you'll tune sensitivity).
No daemon, no SQLite, no API yet.

---

## Phase 2 — Memory  ·  ~2 hrs

**Objective:** Give Rai persistent local state it can read and append to by
voice. This is the "develops over time" piece — it knows more each week because
it logs.

**Dependencies:** none new (`sqlite3` ships with Python).

**Files:** modify `rai.py`; create `rai.db` automatically on first run.

**Schema — three tables:**
- `tasks(id, text, status, created_at, due)` — status in {open, done}
- `money(id, type, amount, note, created_at)` — type in {earned, spent}
- `progress(id, area, note, created_at)` — free-form progress log

**Behavior:**
- On startup, create `rai.db` and the tables if they don't exist.
- Add a small set of spoken logging commands handled before the launcher match:
  - "rai log task &lt;text&gt;" → insert into `tasks` (status open)
  - "rai task done &lt;text&gt;" → mark matching open task done
  - "rai log earned &lt;amount&gt;" / "rai log spent &lt;amount&gt;" → insert into `money`
  - "rai log progress &lt;text&gt;" → insert into `progress`
- Speak a confirmation after each write (e.g. "Logged.").
- Keep all DB access in small helper functions (`add_task`, `complete_task`,
  `add_money`, `add_progress`, plus read helpers) so Phase 3 can reuse them.

**Done when:**
- You can speak data in, restart Rai, and the data is still there.
- Each table can be written and read via the helpers.

**Constraints:** still single file. Input is voice/text only — **no bank sync,
no OCR, no automatic money tracking.** Those are out of scope for the whole
roadmap unless explicitly added later.

---

## Phase 3 — Claude API brain  ·  ~3–4 hrs

**Objective:** Replace fixed keyword matching with natural language. Rai
understands a spoken sentence, reads its own DB plus the current date, and
answers "what should I do today / next / tomorrow?" out loud.

**Dependencies:** Claude API (direct HTTP call to `https://api.anthropic.com/v1/messages`);
`python-dotenv` for secret loading.

**Config / secrets:**
- Load secrets at startup via `python-dotenv` (`load_dotenv()` called once at
  the top of `rai.py`). Store them in a `.env` file in the `rai/` folder —
  never commit it (add `.env` to `.gitignore`).
- Required var: `RAI_CLAUDE_API_KEY` — used as the `x-api-key` request header.
  If missing, print a clear message and exit. Never hardcode.
- Optional var: `RAI_MODEL` — default to a Haiku-class model for routine calls
  to keep cost near the ~₹500/month target.
- Send `x-api-key` and `anthropic-version` headers on every request (correct
  for direct Anthropic API calls). No proxy URL anywhere in the code.

Securing the key behind a Cloudflare Worker proxy is a later hardening step,
only needed if Rai's brain ships inside a public product, not for personal use.

**Behavior:**
1. After the wake word, transcribe the full spoken request as before.
2. If it matches a simple launcher command or a Phase 2 log command, handle it
   locally (fast, free) — don't call the API for those.
3. Otherwise, build a prompt for Claude that includes: today's date, the open
   tasks, recent money entries, recent progress, and the user's question. Ask
   Claude to reply with a short, spoken-friendly answer (2–4 sentences).
4. Speak the reply via `say` and print it.
5. Wrap the API call in try/except; on failure, speak a graceful fallback and
   keep listening.

**Done when:**
- Asking "Rai, what should I do today?" returns a sensible spoken plan grounded
  in your actual logged tasks and the date.
- Simple commands ("open Chrome", logging) still work without hitting the API.

**Constraints:** route routine work locally to control cost. Keep the API prompt
small (only relevant recent rows, not the whole DB).

---

## Phase 4 — Background daemon  ·  ~1–2 hrs  ·  STATUS: DONE

**Objective:** Rai auto-starts on login and runs invisibly — no terminal.

**Files:** add a macOS LaunchAgent plist (e.g.
`~/Library/LaunchAgents/com.partha.rai.plist`); add a short README section on
load/unload.

**Behavior:**
- LaunchAgent runs `rai.py` at login and keeps it alive.
- Logs (stdout/stderr) redirect to a file (e.g. `~/rai.log`) so you can debug
  without a visible terminal.
- Document `launchctl load`/`unload` commands.

**Done when:**
- After a reboot, Rai is already listening with no terminal open.
- Errors land in the log file.

**Constraints:** do this only after Phases 1–3 are stable — debugging a wake word
with no visible terminal is painful.

---

## Phase 5 — Proactive PA + product tracker  ·  Ongoing

**Objective:** Rai stops being purely reactive. It gives an unprompted morning
briefing and becomes the control panel for the product pipeline.

**Behavior (build incrementally, smallest first):**
- Morning briefing: at a set time, Rai speaks "Here's today" — top open tasks,
  yesterday's money summary, one nudge. (Schedule via the LaunchAgent or an
  in-process timer.)
- Product pipeline: extend the schema with a `products` table
  (`id, name, store, status, price, sold_count, created_at`) and voice/text
  commands to add a product, mark it shipped, and log a sale. Rai can answer
  "what did I ship this week?" and "what should I build next?".

**Done when:** Rai opens your day for you and tracks shipped products and sales.

**Constraints:** add one capability at a time and live with it before the next.
Resist turning this into ten half-finished features.

---

## Out of scope (whole project, unless explicitly added later)

- Automatic bank/UPI sync or transaction import
- OCR of receipts or screenshots for money tracking
- Cloud sync / multi-device
- Any second credential beyond the Claude API key

Voice/text input gives ~90% of the value at ~10% of the effort. Start there.
