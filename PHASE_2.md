# Phase 2 — Memory

**Goal:** Give Rai persistent local state it can read and write by voice.  
**Est. time:** ~2 hrs  
**File:** `rai.py` only. DB file `rai.db` is created automatically on first run.

---

## Part 1 — DB Initialization

**Scope:** Add `init_db()` and call it at startup.

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',   -- 'open' | 'done'
    created_at TEXT NOT NULL,
    due TEXT                                -- optional, ISO date
);

CREATE TABLE IF NOT EXISTS money (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                    -- 'earned' | 'spent'
    amount REAL NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    area TEXT,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

**Done when:**
- `rai.db` is created on first run with all three tables.
- Restarting does not error or reset data.

---

## Part 2 — DB Helper Functions

**Scope:** Add write and read helpers for all three tables. No voice wiring yet — just the functions.

**Write helpers:**
- `add_task(text)` — insert into `tasks` with `status='open'` and `created_at=now`
- `complete_task(text)` — set `status='done'` on the first open task whose `text` contains the given substring
- `add_money(type, amount, note="")` — insert into `money`
- `add_progress(note, area="")` — insert into `progress`

**Read helpers (used in Phase 3 for context building, but write them now):**
- `get_open_tasks()` → list of dicts
- `get_recent_money(n=10)` → list of dicts
- `get_recent_progress(n=10)` → list of dicts

**Done when:**
- All helpers are callable from a Python shell and produce correct rows in `rai.db`.
- `complete_task` gracefully does nothing (prints a warning) if no matching task found.

---

## Part 3 — Voice Command Parsing

**Scope:** Add a `parse_memory_command(text)` function that matches the logging utterances and returns a structured action dict (or `None` if no match).

**Patterns to match** (after lowercasing the transcription):

| Utterance | Action |
|---|---|
| `"log task <text>"` | `{action: "add_task", text: "<text>"}` |
| `"task done <text>"` | `{action: "complete_task", text: "<text>"}` |
| `"log earned <amount>"` | `{action: "add_money", type: "earned", amount: float}` |
| `"log spent <amount>"` | `{action: "add_money", type: "spent", amount: float}` |
| `"log progress <text>"` | `{action: "add_progress", note: "<text>"}` |

**Parsing notes:**
- Match on substring presence (no regex needed for most cases).
- For amounts, extract the first number-like token after "earned"/"spent" using a simple `re.search(r"[\d.]+", ...)`.
- Return `None` for anything that doesn't match — it falls through to the existing launcher.

**Done when:**
- `parse_memory_command("log task finish roadmap")` → `{action: "add_task", text: "finish roadmap"}`
- `parse_memory_command("log earned 500")` → `{action: "add_money", type: "earned", amount: 500.0}`
- `parse_memory_command("open chrome")` → `None`

---

## Part 4 — Integration & Spoken Confirmation

**Scope:** Wire `parse_memory_command()` into the main command loop so memory commands are handled before the launcher lookup. Speak a confirmation after each write.

**Integration point** (in the existing post-wake-word flow):

```
transcribe command
  → parse_memory_command(text)
      → if match: call helper, say confirmation, continue listening
      → else: match_command() + run_command()  (existing Phase 1 path)
```

**Confirmation phrases:**
| Action | Spoken confirmation |
|---|---|
| add_task | `"Task logged."` |
| complete_task (found) | `"Task marked done."` |
| complete_task (not found) | `"No matching task found."` |
| add_money (earned) | `"Logged earnings."` |
| add_money (spent) | `"Logged expense."` |
| add_progress | `"Progress logged."` |

**Done when (Phase 2 complete):**
- "Rai, log task finish the landing page" → task appears in `rai.db`, Rai says "Task logged."
- "Rai, task done finish the landing page" → status flips to `done`.
- "Rai, log earned 2000" → money row inserted.
- "Rai, log progress shipped the new feature" → progress row inserted.
- Restart Rai — all rows are still there.
- "Rai, open Chrome" still works (launcher path unbroken).

---

## Implementation order

1. Part 1 (DB init) → verify tables exist
2. Part 2 (helpers) → test in Python shell
3. Part 3 (parser) → test with print statements
4. Part 4 (integration) → full end-to-end voice test
