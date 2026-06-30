#!/usr/bin/env python3
"""
Rai — always-on voice-command app launcher for macOS.

Say "Rai" as the wake word, then speak a command, and Rai opens the matching
app or URL. Everything runs locally; no cloud APIs or credentials needed.
"""

import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel

load_dotenv()  # reads rai/.env into os.environ at startup

# --- Config -------------------------------------------------------------------
WAKE_WORD = "alex"
WAKE_WORD_VARIANTS = ["alex", "alexa", "alec", "alix"]  # faster-whisper mishears
CHUNK_SECONDS = 2
HOP_SECONDS = 1               # advance by 1s, keep last 1s → 2s overlapping window
RMS_THRESHOLD = 0.005         # below this volume, skip Whisper entirely
COMMAND_RECORD_SECONDS = 4
FOLLOWUP_TIMEOUT = 8          # seconds to wait for a follow-up before sleeping
SAMPLE_RATE = 16_000          # Hz, mono — Whisper expects 16 kHz
WHISPER_MODEL = "base.en"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8" # ~75 MB RAM on CPU
DB_PATH = "rai.db"

# Phase 5: morning briefing — fires once when local time first reaches this
BRIEFING_TIME = "09:00"  # 24h "HH:MM", local time

# Phase 3: Claude API — key loaded from .env via python-dotenv above
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
RAI_CLAUDE_API_KEY = os.environ.get("RAI_CLAUDE_API_KEY", "")
RAI_MODEL          = os.environ.get("RAI_MODEL", "claude-haiku-4-5-20251001")

# Spoken phrase (substring) -> macOS command list passed to subprocess.run().
COMMANDS = {
    # Apps
    "chrome": ["open", "-a", "Google Chrome"],
    "vs code": ["open", "-a", "Visual Studio Code"],
    "vscode": ["open", "-a", "Visual Studio Code"],
    "code": ["open", "-a", "Visual Studio Code"],
    # WhatsApp.app on this Mac has a hidden U+200E mark before its name, so
    # `open -a WhatsApp` can't resolve it by name — open the bundle path instead.
    "whatsapp": ["open", "/Applications/‎WhatsApp.app"],
    "what's up": ["open", "/Applications/‎WhatsApp.app"],  # base.en mishears "WhatsApp" phonetically
    "whats up": ["open", "/Applications/‎WhatsApp.app"],
    "spotify": ["open", "-a", "Spotify"],
    "terminal": ["open", "-a", "Terminal"],
    "finder": ["open", "-a", "Finder"],
    "notes": ["open", "-a", "Notes"],
    # Websites
    "amazon": ["open", "https://www.amazon.com"],
    "youtube": ["open", "https://www.youtube.com"],
    "gmail": ["open", "https://mail.google.com"],
    "github": ["open", "https://github.com"],
}


def init_db() -> None:
    """Create rai.db and all tables if they don't already exist."""
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            text       TEXT    NOT NULL,
            status     TEXT    NOT NULL DEFAULT 'open',
            created_at TEXT    NOT NULL,
            due        TEXT
        );

        CREATE TABLE IF NOT EXISTS money (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            type       TEXT    NOT NULL,
            amount     REAL    NOT NULL,
            note       TEXT,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS progress (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            area       TEXT,
            note       TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            store      TEXT,
            status     TEXT    NOT NULL DEFAULT 'building',
            price      REAL,
            sold_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    NOT NULL
        );
    """)
    con.commit()
    con.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Part 2: DB helpers -------------------------------------------------------

def add_task(text: str) -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO tasks (text, status, created_at) VALUES (?, 'open', ?)",
            (text, _now()),
        )


def complete_task(text: str) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT id FROM tasks WHERE status='open' AND text LIKE ? LIMIT 1",
            (f"%{text}%",),
        )
        row = cur.fetchone()
        if row is None:
            print(f"[warn] no open task matching '{text}'")
            return False
        con.execute("UPDATE tasks SET status='done' WHERE id=?", (row[0],))
    return True


def add_money(type_: str, amount: float, note: str = "") -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO money (type, amount, note, created_at) VALUES (?, ?, ?, ?)",
            (type_, amount, note, _now()),
        )


def add_progress(note: str, area: str = "") -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO progress (area, note, created_at) VALUES (?, ?, ?)",
            (area, note, _now()),
        )


def get_open_tasks() -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM tasks WHERE status='open' ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_money(n: int = 10) -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM money ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_progress(n: int = 10) -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM progress ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_product(name: str, store: str = "", price: Optional[float] = None) -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO products (name, store, status, price, sold_count, created_at) VALUES (?, ?, 'building', ?, 0, ?)",
            (name, store, price, _now()),
        )


def ship_product(name: str) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT id FROM products WHERE name LIKE ? LIMIT 1",
            (f"%{name}%",),
        )
        row = cur.fetchone()
        if row is None:
            print(f"[warn] no product matching '{name}'")
            return False
        con.execute("UPDATE products SET status='shipped' WHERE id=?", (row[0],))
    return True


def log_sale(name: str) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT id FROM products WHERE name LIKE ? LIMIT 1",
            (f"%{name}%",),
        )
        row = cur.fetchone()
        if row is None:
            print(f"[warn] no product matching '{name}'")
            return False
        con.execute("UPDATE products SET sold_count = sold_count + 1 WHERE id=?", (row[0],))
    return True


def get_products() -> list[dict]:
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT * FROM products ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_money_totals_for_date(date_obj) -> Tuple[float, float]:
    """Return (total_earned, total_spent) for the given local calendar date.

    created_at is stored as UTC; this filters on the UTC date, same as
    _build_prompt's "today" already treats local and UTC dates as equivalent.
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT type, SUM(amount) FROM money WHERE date(created_at) = ? GROUP BY type",
            (date_str,),
        ).fetchall()
    totals = {"earned": 0.0, "spent": 0.0}
    for type_, total in rows:
        totals[type_] = total or 0.0
    return totals["earned"], totals["spent"]


# --- Phase 3: Claude API brain ------------------------------------------------

def _check_api_config() -> None:
    if not RAI_CLAUDE_API_KEY:
        print("[error] Missing RAI_CLAUDE_API_KEY.")
        print("Add it to rai/.env:  RAI_CLAUDE_API_KEY=sk-ant-...")
        sys.exit(1)


def _build_prompt(question: str) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    tasks    = get_open_tasks()
    money    = get_recent_money(5)
    progress = get_recent_progress(5)
    products = get_products()

    task_lines     = "\n".join(f"- {t['text']}" for t in tasks) or "None"
    money_lines    = "\n".join(
        f"- {m['type']} {m['amount']}" + (f" ({m['note']})" if m.get("note") else "")
        for m in money
    ) or "None"
    progress_lines = "\n".join(f"- {p['note']}" for p in progress) or "None"
    product_lines  = "\n".join(
        f"- {p['name']} [{p['status']}]"
        + (f" store:{p['store']}" if p.get("store") else "")
        + (f" price:{p['price']}" if p.get("price") is not None else "")
        + f" sales:{p['sold_count']}"
        for p in products
    ) or "None"

    return (
        f"Today is {today}.\n\n"
        f"Open tasks:\n{task_lines}\n\n"
        f"Recent money entries:\n{money_lines}\n\n"
        f"Recent progress:\n{progress_lines}\n\n"
        f"Products:\n{product_lines}\n\n"
        f"User question: {question}\n\n"
        "Reply in 2-4 sentences. Be concise and spoken-friendly — no bullet points, no markdown."
    )


def ask_claude(question: str) -> str:
    payload = json.dumps({
        "model": RAI_MODEL,
        "max_tokens": 256,
        "system": (
            "You are Rai, a personal assistant. Answer the user's question using "
            "the tasks, money, and progress data provided. Keep replies short and "
            "natural — 2 to 4 spoken sentences, no lists or markdown."
        ),
        "messages": [{"role": "user", "content": _build_prompt(question)}],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": RAI_CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read())
    return body["content"][0]["text"].strip()


# --- Phase 5: morning briefing -------------------------------------------------

def build_morning_briefing() -> str:
    """Build the spoken "here's today" summary: top tasks, yesterday's money, one nudge."""
    tasks = get_open_tasks()
    top_tasks = tasks[:3]
    earned, spent = get_money_totals_for_date(datetime.now() - timedelta(days=1))

    if top_tasks:
        task_part = "Top tasks: " + "; ".join(t["text"] for t in top_tasks) + "."
    else:
        task_part = "You have no open tasks."

    money_part = f"Yesterday you earned {earned:.0f} and spent {spent:.0f}."

    if not tasks:
        nudge = "You're all caught up — good day to plan ahead."
    elif len(tasks) > 5:
        nudge = f"You have {len(tasks)} open tasks piling up — consider clearing a few today."
    else:
        nudge = "Have a productive day."

    return f"Here's today. {task_part} {money_part} {nudge}"


# --- Part 3: Voice command parser ---------------------------------------------

def parse_memory_command(text: str) -> Optional[dict]:
    t = text.lower().strip()

    if t.startswith("log task "):
        return {"action": "add_task", "text": text[len("log task "):].strip()}

    if t.startswith("task done "):
        return {"action": "complete_task", "text": text[len("task done "):].strip()}

    if "log earned" in t:
        m = re.search(r"[\d.]+", t[t.index("log earned") + len("log earned"):])
        if m:
            return {"action": "add_money", "type": "earned", "amount": float(m.group())}

    if "log spent" in t:
        m = re.search(r"[\d.]+", t[t.index("log spent") + len("log spent"):])
        if m:
            return {"action": "add_money", "type": "spent", "amount": float(m.group())}

    if t.startswith("log progress "):
        return {"action": "add_progress", "note": text[len("log progress "):].strip()}

    if t.startswith("add product "):
        return {"action": "add_product", "name": text[len("add product "):].strip()}

    if t.startswith("ship product "):
        return {"action": "ship_product", "name": text[len("ship product "):].strip()}

    if t.startswith("mark shipped "):
        return {"action": "ship_product", "name": text[len("mark shipped "):].strip()}

    if t.startswith("log sale "):
        return {"action": "log_sale", "name": text[len("log sale "):].strip()}

    return None


def execute_memory_command(action: dict) -> str:
    """Run a parsed memory action; return the spoken confirmation string."""
    a = action["action"]
    if a == "add_task":
        add_task(action["text"])
        return "Task logged."
    if a == "complete_task":
        found = complete_task(action["text"])
        return "Task marked done." if found else "No matching task found."
    if a == "add_money":
        add_money(action["type"], action["amount"])
        return "Logged earnings." if action["type"] == "earned" else "Logged expense."
    if a == "add_progress":
        add_progress(action["note"])
        return "Progress logged."
    if a == "add_product":
        add_product(action["name"])
        return "Product added."
    if a == "ship_product":
        found = ship_product(action["name"])
        return "Product marked shipped." if found else "No matching product found."
    if a == "log_sale":
        found = log_sale(action["name"])
        return "Sale logged." if found else "No matching product found."
    return ""


def record_audio(seconds: float, sample_rate: int) -> np.ndarray:
    """Record mono audio from the default microphone."""
    frames = int(seconds * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def transcribe(model: WhisperModel, audio: np.ndarray) -> str:
    """Transcribe audio locally with faster-whisper; return lowercase text."""
    segments, _ = model.transcribe(audio, language="en")
    text = " ".join(segment.text for segment in segments).strip().lower()
    return text


def match_command(transcript: str) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Find the first COMMANDS entry whose phrase appears in the transcript.

    Longer phrases are checked first so "vs code" wins over "code".
    """
    for phrase in sorted(COMMANDS, key=len, reverse=True):
        if phrase in transcript:
            return phrase, COMMANDS[phrase]
    return None, None


def run_command(cmd: list[str]) -> None:
    """Run a macOS open command."""
    subprocess.run(cmd, check=True)


def speak(text: str) -> None:
    """Speak text via macOS say."""
    subprocess.run(["say", text])


def process_transcript(transcript: str, speak_output: bool = True) -> None:
    """Match a transcript against memory actions or launchers, else ask Claude.

    Shared by the voice path (handle_command) and chat_mode, so typed
    commands get identical matching behavior to spoken ones.
    """
    if not transcript:
        print("Heard nothing — try speaking clearly.\n")
        if speak_output:
            speak("I didn't catch that")
        return

    print(f'Heard: "{transcript}"')

    action = parse_memory_command(transcript)
    if action is not None:
        confirmation = execute_memory_command(action)
        print(f'Memory action: {action["action"]} → "{confirmation}"')
        if speak_output:
            speak(confirmation)
        print()
        return

    phrase, cmd = match_command(transcript)
    if phrase is not None:
        print(f'Matched: "{phrase}" → {" ".join(cmd)}')
        run_command(cmd)
        if speak_output:
            speak(f"Opening {phrase}")
        print("Done.\n")
        return

    # Neither a launcher nor a memory command — ask Claude.
    print("Asking Claude…")
    try:
        reply = ask_claude(transcript)
        print(f'Claude: "{reply}"')
        if speak_output:
            speak(reply)
    except Exception as exc:
        print(f"[error] Claude API call failed: {exc}")
        if speak_output:
            speak("Sorry, I couldn't reach the assistant right now")
    print()


def handle_command(model: WhisperModel) -> None:
    """Record a command, transcribe, match, run, and speak confirmation."""
    print(f"Listening for command ({COMMAND_RECORD_SECONDS}s)…")
    audio = record_audio(COMMAND_RECORD_SECONDS, SAMPLE_RATE)

    print("Transcribing…")
    transcript = transcribe(model, audio)
    process_transcript(transcript)


def chat_mode() -> None:
    """Text-only REPL: type commands instead of speaking them.

    No microphone or Whisper involved — same matching/Claude logic as
    voice mode via process_transcript(). Exit with 'quit', 'exit', or Ctrl+C/D.
    """
    _check_api_config()
    init_db()
    print("Rai chat mode. Type a command (e.g. 'open chrome'), or 'quit' to exit.\n")
    while True:
        try:
            line = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line in ("quit", "exit"):
            break
        if not line:
            continue
        process_transcript(line, speak_output=False)


def listen_for_followup(model: WhisperModel) -> bool:
    """
    Listen for one follow-up command without requiring the wake word.

    Polls overlapping HOP_SECONDS windows for up to FOLLOWUP_TIMEOUT seconds.
    On detecting speech, hands off to handle_command() (which does its own
    fixed-length recording) and returns True so the caller re-enters this
    function and the follow-up window resets. Returns False once
    FOLLOWUP_TIMEOUT elapses with no speech, meaning Rai should go back to
    wake-word-only listening.
    """
    print(f"Listening for follow-up (up to {FOLLOWUP_TIMEOUT}s)…")
    hop_frames = int(HOP_SECONDS * SAMPLE_RATE)
    prev_hop = np.zeros(hop_frames, dtype="float32")
    elapsed = 0.0

    while elapsed < FOLLOWUP_TIMEOUT:
        new_hop = sd.rec(hop_frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        new_hop = new_hop.flatten()
        elapsed += HOP_SECONDS

        chunk = np.concatenate([prev_hop, new_hop])
        prev_hop = new_hop

        rms = float(np.sqrt(np.mean(chunk ** 2)))
        if rms < RMS_THRESHOLD:
            continue

        print("Follow-up speech detected.")
        handle_command(model)
        return True

    return False


def main() -> None:
    _check_api_config()
    init_db()
    print("Loading Whisper model (first run may download weights)…")
    model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)
    print("Whisper loaded.")
    print("Rai is listening for the wake word…\n")

    hop_frames = int(HOP_SECONDS * SAMPLE_RATE)

    # Sliding window: keep the previous hop so wake word isn't missed at chunk boundaries.
    prev_hop = np.zeros(hop_frames, dtype="float32")

    # Phase 5: morning briefing fires once per calendar day at BRIEFING_TIME.
    last_briefing_date: Optional[str] = None

    try:
        while True:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            if now.strftime("%H:%M") == BRIEFING_TIME and last_briefing_date != today_str:
                briefing = build_morning_briefing()
                print(f"\nMorning briefing: {briefing}\n")
                speak(briefing)
                last_briefing_date = today_str

            new_hop = sd.rec(hop_frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            new_hop = new_hop.flatten()

            chunk = np.concatenate([prev_hop, new_hop])
            prev_hop = new_hop

            # Skip Whisper on silence — faster-whisper hallucinates on quiet audio
            # (returns things like "you" or "Thank you."), causing false wake-word
            # triggers. The RMS gate prevents this and saves CPU.
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            print(f"[RMS: {rms:.4f}]", end="\r")

            if rms < RMS_THRESHOLD:
                continue

            text = transcribe(model, chunk)
            print(f"[RMS: {rms:.4f}] Heard: \"{text}\"")

            if any(variant in text for variant in WAKE_WORD_VARIANTS):
                print("Wake word detected!")
                speak("Yes?")
                handle_command(model)
                prev_hop = np.zeros(hop_frames, dtype="float32")

                # Conversation mode: keep listening without the wake word
                # until FOLLOWUP_TIMEOUT passes with no speech.
                while listen_for_followup(model):
                    pass
                print("Going back to sleep.")
                prev_hop = np.zeros(hop_frames, dtype="float32")

    except KeyboardInterrupt:
        print("\nRai stopped.")
        sys.exit(0)


if __name__ == "__main__":
    if "--chat" in sys.argv:
        chat_mode()
    else:
        main()
