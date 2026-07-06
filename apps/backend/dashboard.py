#!/usr/bin/env python3
"""
Nova Dashboard — Phase 16: full dashboard view with sidebar nav.

Run alongside nova.py:
    cd apps/backend && uvicorn dashboard:app --port 8000
Or directly:
    cd apps/backend && python dashboard.py

Reads nova.db only via the memory/ package — never writes, never touches
sqlite3 directly. Serves http://localhost:8000
Calendar events fetched live from macOS Calendar via osascript (cached 60s).
"""

import re
import subprocess
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import identity
import memory
from paths import REPO_ROOT

load_dotenv(REPO_ROOT / ".env")

app = FastAPI(title=f"{identity.ASSISTANT_NAME} Dashboard")

_cal_cache: dict = {"ts": 0.0, "data": {"events": [], "unavailable": False}}


def _rel(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        if s < 60:
            return "just now"
        if s < 3600:
            return f"{s // 60}m ago"
        if s < 86400:
            return f"{s // 3600}h ago"
        return f"{s // 86400}d ago"
    except Exception:
        return iso[:10]


def _summary() -> dict:
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    earned, spent = memory.get_money_totals_between(month_start, today)
    return {
        "reminder_count": memory.count_reminders(),
        "task_count": memory.count_open_tasks(),
        "earned_month": earned,
        "spent_month": spent,
    }


def _reminders() -> list:
    out = []
    for r in memory.get_upcoming_reminders(20):
        try:
            dt = datetime.strptime(r["remind_date"], "%Y-%m-%d")
            delta = (dt.date() - datetime.now().date()).days
            if delta == 0:
                label = "Today"
            elif delta == 1:
                label = "Tomorrow"
            elif delta <= 7:
                label = dt.strftime("%A")
            else:
                label = dt.strftime("%b %d")
            urgent = delta <= 1
        except Exception:
            label = r["remind_date"]
            urgent = False
        out.append({"text": r["text"], "date": r["remind_date"], "label": label, "urgent": urgent})
    return out


def _todos() -> list:
    return [{"text": t["text"], "due": t["due"]} for t in memory.get_open_tasks(limit=20)]


def _feed() -> list:
    events = []

    for r in memory.get_recent_tasks(5):
        label = r["text"]
        if r["status"] == "done":
            label = f"✓ {label}"
        events.append({"kind": "task", "label": label, "ts": r["created_at"]})

    for r in memory.get_recent_money(5):
        note = f" · {r['note']}" if r["note"] else ""
        arrow = "↑" if r["type"] == "earned" else "↓"
        events.append(
            {"kind": "money", "label": f"{arrow} ₹{r['amount']:.0f}{note}", "ts": r["created_at"]}
        )

    for r in memory.get_recent_progress(5):
        prefix = f"[{r['area']}] " if r["area"] else ""
        events.append({"kind": "progress", "label": f"{prefix}{r['note']}", "ts": r["created_at"]})

    for r in memory.get_recent_reminders(5):
        events.append(
            {
                "kind": "reminder",
                "label": f"Reminder set · {r['text']} · {r['remind_date']}",
                "ts": r["created_at"],
            }
        )

    for r in memory.get_recent_habits(5):
        events.append({"kind": "habit", "label": f"Habit · {r['name']}", "ts": r["created_at"]})

    events.sort(key=lambda x: x["ts"], reverse=True)
    for e in events[:15]:
        e["ago"] = _rel(e["ts"])
    return events[:15]


def _get_today_events() -> dict:
    """Fetch today's calendar events from macOS Calendar via AppleScript (cached 60s)."""
    now_t = time.time()
    if now_t - _cal_cache["ts"] < 60:
        return _cal_cache["data"]

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def _date_block(var: str, dt: datetime) -> str:
        return (
            f"  set {var} to current date\n"
            f"  set year of {var} to {dt.year}\n"
            f"  set month of {var} to {dt.month}\n"
            f"  set day of {var} to {dt.day}\n"
            f"  set hours of {var} to {dt.hour}\n"
            f"  set minutes of {var} to {dt.minute}\n"
            f"  set seconds of {var} to 0\n"
        )

    script = "".join(
        [
            'tell application "Calendar"\n',
            _date_block("startBound", today),
            f"  set endBound to startBound + {23 * 3600 + 59 * 60 + 59}\n",
            '  set output to ""\n',
            "  repeat with cal in calendars\n",
            "    try\n",
            "      repeat with e in (every event of cal)\n",
            "        set sd to start date of e\n",
            "        if sd >= startBound and sd <= endBound then\n",
            '          set output to output & (summary of e) & "|" & (time string of sd) & "\\n"\n',
            "        end if\n",
            "      end repeat\n",
            "    end try\n",
            "  end repeat\n",
            "  return output\n",
            "end tell\n",
        ]
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            data = {"events": [], "unavailable": True}
        else:
            evts = []
            for line in result.stdout.strip().splitlines():
                if "|" in line:
                    title_part, time_part = line.split("|", 1)
                    time_clean = re.sub(r":00(?=[  ][AP]M)", "", time_part.strip())
                    time_clean = time_clean.replace(" ", " ")
                    evts.append({"title": title_part.strip(), "time": time_clean})
            data = {"events": evts, "unavailable": False}
    except Exception:
        data = {"events": [], "unavailable": True}

    _cal_cache["ts"] = time.time()
    _cal_cache["data"] = data
    return data


def _get_profile() -> list:
    try:
        return [
            {
                "observation": o["observation"],
                "category": o["category"],
                "confidence": o["confidence"],
            }
            for o in memory.get_profile_observations()
        ]
    except Exception:
        return []


def _get_money_detail() -> dict:
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    earned, spent = memory.get_money_totals_between(month_start, today)
    transactions = [
        {
            "type": r["type"],
            "amount": r["amount"],
            "note": r["note"] or "",
            "ago": _rel(r["created_at"]),
        }
        for r in memory.get_recent_money(30)
    ]
    return {
        "earned_month": earned,
        "spent_month": spent,
        "transactions": transactions,
    }


@app.get("/api/data")
def api_data():
    return JSONResponse(
        {
            "summary": _summary(),
            "reminders": _reminders(),
            "todos": _todos(),
            "feed": _feed(),
            "ts": datetime.now().strftime("%H:%M:%S"),
        }
    )


@app.get("/api/calendar")
def api_calendar():
    return JSONResponse(_get_today_events())


@app.get("/api/profile")
def api_profile():
    return JSONResponse({"observations": _get_profile()})


@app.get("/api/money")
def api_money():
    return JSONResponse(_get_money_detail())


_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nova</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e2e8f0;
    --muted: #6b7280;
    --accent: #6366f1;
    --green: #10b981;
    --red: #ef4444;
    --yellow: #f59e0b;
    --blue: #3b82f6;
    --purple: #a78bfa;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; font-size: 14px; height: 100vh; display: flex; overflow: hidden; }

  /* Sidebar */
  .sidebar { width: 196px; background: var(--surface); border-right: 1px solid var(--border); display: flex; flex-direction: column; flex-shrink: 0; }
  .sidebar-logo { padding: 20px 16px 16px; font-size: 20px; font-weight: 700; letter-spacing: -.5px; border-bottom: 1px solid var(--border); }
  .sidebar-logo span { color: var(--accent); }
  .sidebar-nav { flex: 1; padding: 10px 0; }
  .nav-item { display: flex; align-items: center; gap: 9px; padding: 9px 14px; cursor: pointer; border-radius: 7px; margin: 1px 8px; color: var(--muted); transition: background .12s, color .12s; }
  .nav-item:hover { background: rgba(255,255,255,.05); color: var(--text); }
  .nav-item.active { background: rgba(99,102,241,.15); color: var(--accent); }
  .nav-icon { width: 16px; text-align: center; font-size: 13px; flex-shrink: 0; }
  .nav-label { font-size: 13px; font-weight: 500; }
  .sidebar-footer { padding: 12px 16px; border-top: 1px solid var(--border); }
  .ts-row { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; flex-shrink: 0; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  /* Content */
  .content { flex: 1; overflow-y: auto; }
  .view { display: none; padding: 28px; max-width: 1020px; }
  .view.active { display: block; }
  .view-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; }

  /* Metric cards */
  .metrics { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 16px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .card-label { font-size: 11px; text-transform: uppercase; letter-spacing: .6px; color: var(--muted); margin-bottom: 8px; }
  .card-value { font-size: 26px; font-weight: 700; line-height: 1; }
  .card-value.green { color: var(--green); }
  .card-value.red   { color: var(--red); }
  .card-value.blue  { color: var(--blue); }

  /* Panel */
  .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 16px; }
  .panel-head { padding: 11px 16px; border-bottom: 1px solid var(--border); font-weight: 600; font-size: 13px; display: flex; align-items: center; justify-content: space-between; }
  .panel-count { font-size: 11px; color: var(--muted); font-weight: 400; }
  .panel-body { padding: 6px 0; }

  /* Two-col layout */
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }

  /* Rows */
  .row { display: flex; align-items: flex-start; gap: 10px; padding: 8px 16px; }
  .row:hover { background: rgba(255,255,255,.03); }
  .row-icon { font-size: 14px; margin-top: 1px; flex-shrink: 0; }
  .row-text { flex: 1; min-width: 0; }
  .row-main { line-height: 1.4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .row-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .badge { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 4px; font-weight: 600; margin-left: 6px; }
  .badge.today { background: rgba(239,68,68,.2); color: var(--red); }
  .badge.tmrw  { background: rgba(245,158,11,.2); color: var(--yellow); }
  .empty { padding: 22px 16px; color: var(--muted); font-size: 13px; text-align: center; }

  /* Activity feed */
  .kind-task     { color: var(--blue); }
  .kind-money    { color: var(--green); }
  .kind-progress { color: var(--accent); }
  .kind-reminder { color: var(--yellow); }
  .kind-habit    { color: var(--purple); }

  /* Today strip */
  .today-strip { display: flex; gap: 10px; padding: 14px 16px; overflow-x: auto; flex-wrap: wrap; min-height: 60px; align-items: center; }
  .event-chip { background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.25); border-radius: 8px; padding: 8px 12px; flex-shrink: 0; }
  .event-chip-title { font-size: 13px; font-weight: 500; }
  .event-chip-time  { font-size: 11px; color: var(--muted); margin-top: 2px; }

  /* Money bars */
  .money-bars { padding: 16px; }
  .money-bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .money-bar-row:last-child { margin-bottom: 0; }
  .money-bar-label { font-size: 12px; color: var(--muted); width: 48px; text-align: right; flex-shrink: 0; }
  .money-bar-track { flex: 1; height: 10px; background: rgba(255,255,255,.06); border-radius: 99px; overflow: hidden; }
  .money-bar-fill { height: 100%; border-radius: 99px; transition: width .5s ease; min-width: 0; }
  .money-bar-fill.earned { background: var(--green); }
  .money-bar-fill.spent  { background: var(--red); }
  .money-bar-amount { font-size: 13px; font-weight: 600; width: 90px; flex-shrink: 0; }
  .money-bar-amount.earned { color: var(--green); }
  .money-bar-amount.spent  { color: var(--red); }

  /* Profile observations */
  .obs-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 16px; }
  .obs-row:hover { background: rgba(255,255,255,.03); }
  .obs-meta { flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; padding-top: 2px; }
  .cat-tag { font-size: 10px; padding: 2px 7px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; white-space: nowrap; }
  .cat-habits      { background: rgba(167,139,250,.15); color: var(--purple); }
  .cat-work        { background: rgba(59,130,246,.15);  color: var(--blue); }
  .cat-finances    { background: rgba(16,185,129,.15);  color: var(--green); }
  .cat-productivity{ background: rgba(99,102,241,.15);  color: var(--accent); }
  .cat-health      { background: rgba(239,68,68,.15);   color: var(--red); }
  .cat-social      { background: rgba(245,158,11,.15);  color: var(--yellow); }
  .cat-general     { background: rgba(107,114,128,.15); color: var(--muted); }
  .conf-bar { width: 36px; height: 3px; background: rgba(255,255,255,.08); border-radius: 99px; overflow: hidden; }
  .conf-fill { height: 100%; background: var(--accent); border-radius: 99px; }

  /* Transaction rows */
  .tx-row { display: flex; align-items: center; gap: 12px; padding: 9px 16px; }
  .tx-row:hover { background: rgba(255,255,255,.03); }
  .tx-arrow { font-size: 15px; width: 18px; text-align: center; flex-shrink: 0; }
  .tx-note { flex: 1; font-size: 13px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .tx-ago  { font-size: 11px; color: var(--muted); flex-shrink: 0; }
  .tx-amount { font-size: 13px; font-weight: 600; flex-shrink: 0; }
  .tx-amount.earned { color: var(--green); }
  .tx-amount.spent  { color: var(--red); }

  /* Placeholder */
  .placeholder-box { background: var(--surface); border: 1px dashed var(--border); border-radius: 10px; padding: 32px 24px; text-align: center; margin-bottom: 16px; }
  .placeholder-box strong { display: block; font-size: 15px; margin-bottom: 6px; }
  .placeholder-box p { font-size: 13px; color: var(--muted); max-width: 380px; margin: 0 auto; line-height: 1.6; }

  /* Responsive */
  @media(max-width: 640px){
    .sidebar { width: 50px; }
    .nav-label, .sidebar-logo, .sidebar-footer { display: none; }
    .nav-item { justify-content: center; padding: 10px 0; margin: 1px 4px; }
    .nav-icon { width: auto; }
    .metrics { grid-template-columns: repeat(2,1fr); }
    .two-col { grid-template-columns: 1fr; }
    .view { padding: 16px; }
  }
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-logo">R<span>ai</span></div>
  <nav class="sidebar-nav">
    <div class="nav-item active" data-view="home">    <span class="nav-icon">⌂</span><span class="nav-label">Home</span></div>
    <div class="nav-item" data-view="reminders">      <span class="nav-icon">🔔</span><span class="nav-label">Reminders</span></div>
    <div class="nav-item" data-view="todos">          <span class="nav-icon">✓</span><span class="nav-label">Todos</span></div>
    <div class="nav-item" data-view="money">          <span class="nav-icon">₹</span><span class="nav-label">Money</span></div>
    <div class="nav-item" data-view="talk">           <span class="nav-icon">💬</span><span class="nav-label">Talk</span></div>
    <div class="nav-item" data-view="insights">       <span class="nav-icon">✦</span><span class="nav-label">Insights</span></div>
    <div class="nav-item" data-view="settings">       <span class="nav-icon">⚙</span><span class="nav-label">Settings</span></div>
  </nav>
  <div class="sidebar-footer">
    <div class="ts-row"><span class="dot"></span><span id="ts">—</span></div>
  </div>
</div>

<main class="content">

  <!-- ── Home ── -->
  <div id="view-home" class="view active">
    <div class="metrics">
      <div class="card"><div class="card-label">Reminders</div><div class="card-value" id="m-rem">—</div></div>
      <div class="card"><div class="card-label">Open Todos</div><div class="card-value blue" id="m-tasks">—</div></div>
      <div class="card"><div class="card-label">Earned this month</div><div class="card-value green" id="m-earned">—</div></div>
      <div class="card"><div class="card-label">Spent this month</div><div class="card-value red" id="m-spent">—</div></div>
    </div>

    <div class="panel">
      <div class="panel-head">Today <span class="panel-count" id="today-count"></span></div>
      <div id="today-strip" class="today-strip"><span style="color:var(--muted);font-size:13px">Loading…</span></div>
    </div>

    <div class="panel">
      <div class="panel-head">Money This Month</div>
      <div class="money-bars">
        <div class="money-bar-row">
          <div class="money-bar-label">Earned</div>
          <div class="money-bar-track"><div class="money-bar-fill earned" id="hbar-earned" style="width:0%"></div></div>
          <div class="money-bar-amount earned" id="hbar-earned-amt">—</div>
        </div>
        <div class="money-bar-row">
          <div class="money-bar-label">Spent</div>
          <div class="money-bar-track"><div class="money-bar-fill spent" id="hbar-spent" style="width:0%"></div></div>
          <div class="money-bar-amount spent" id="hbar-spent-amt">—</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <div class="panel">
        <div class="panel-head">Upcoming Reminders <span class="panel-count" id="h-rem-count"></span></div>
        <div class="panel-body" id="h-rem-list"><div class="empty">Loading…</div></div>
      </div>
      <div class="panel">
        <div class="panel-head">Open Todos <span class="panel-count" id="h-todo-count"></span></div>
        <div class="panel-body" id="h-todo-list"><div class="empty">Loading…</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head">What Nova Has Learned <span class="panel-count" id="h-profile-count"></span></div>
      <div class="panel-body" id="h-profile-list"><div class="empty">Loading…</div></div>
    </div>

    <div class="panel">
      <div class="panel-head">Live Activity</div>
      <div class="panel-body" id="feed-list"><div class="empty">Loading…</div></div>
    </div>
  </div>

  <!-- ── Reminders ── -->
  <div id="view-reminders" class="view">
    <div class="view-title">Reminders</div>
    <div class="panel">
      <div class="panel-head">All Upcoming <span class="panel-count" id="rem-view-count"></span></div>
      <div class="panel-body" id="rem-view-list"><div class="empty">No upcoming reminders</div></div>
    </div>
  </div>

  <!-- ── Todos ── -->
  <div id="view-todos" class="view">
    <div class="view-title">Todos</div>
    <div class="panel">
      <div class="panel-head">Open Tasks <span class="panel-count" id="todo-view-count"></span></div>
      <div class="panel-body" id="todo-view-list"><div class="empty">All clear — no open todos</div></div>
    </div>
  </div>

  <!-- ── Money ── -->
  <div id="view-money" class="view">
    <div class="view-title">Money</div>
    <div class="panel">
      <div class="panel-head">This Month</div>
      <div class="money-bars">
        <div class="money-bar-row">
          <div class="money-bar-label">Earned</div>
          <div class="money-bar-track"><div class="money-bar-fill earned" id="mbar-earned" style="width:0%"></div></div>
          <div class="money-bar-amount earned" id="mbar-earned-amt">—</div>
        </div>
        <div class="money-bar-row">
          <div class="money-bar-label">Spent</div>
          <div class="money-bar-track"><div class="money-bar-fill spent" id="mbar-spent" style="width:0%"></div></div>
          <div class="money-bar-amount spent" id="mbar-spent-amt">—</div>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head">Recent Transactions</div>
      <div class="panel-body" id="money-tx-list"><div class="empty">No transactions yet</div></div>
    </div>
  </div>

  <!-- ── Talk (Phase 18 placeholder) ── -->
  <div id="view-talk" class="view">
    <div class="view-title">Talk</div>
    <div class="placeholder-box">
      <strong>Conversation view — coming in Phase 18</strong>
      <p>Your spoken exchanges with Nova will appear here as chat bubbles, with inline action cards showing what was saved or done.</p>
    </div>
  </div>

  <!-- ── Insights ── -->
  <div id="view-insights" class="view">
    <div class="view-title">Insights</div>
    <div class="panel">
      <div class="panel-head">What Nova Has Learned <span class="panel-count" id="ins-profile-count"></span></div>
      <div class="panel-body" id="ins-profile-list"><div class="empty">Loading…</div></div>
    </div>
    <div class="placeholder-box">
      <strong>Contextual visualization — coming in Phase 22</strong>
      <p>Charts generated from your data — spending over time, habit streaks, task completion rates — will appear here.</p>
    </div>
  </div>

  <!-- ── Settings (placeholder) ── -->
  <div id="view-settings" class="view">
    <div class="view-title">Settings</div>
    <div class="placeholder-box">
      <strong>Settings — coming in a later phase</strong>
      <p>Wake word, TTS engine, language, briefing time, and notification preferences will be configurable here.</p>
    </div>
  </div>

</main>

<script>
const KIND_ICONS = { task:"📋", money:"💰", progress:"📈", reminder:"🔔", habit:"⚡" };
const CAT_CLASS  = {
  habits:"cat-habits", work:"cat-work", finances:"cat-finances",
  productivity:"cat-productivity", health:"cat-health",
  social:"cat-social", general:"cat-general"
};

function fmt(n){ return "₹" + Number(n).toLocaleString("en-IN", {maximumFractionDigits:0}); }
function esc(s){
  const d = document.createElement("div");
  d.textContent = String(s == null ? "" : s);
  return d.innerHTML;
}

// ── Navigation ──
let currentView = "home";

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => {
    const v = el.dataset.view;
    document.querySelectorAll(".nav-item").forEach(n => n.classList.toggle("active", n === el));
    document.querySelectorAll(".view").forEach(vEl => vEl.classList.toggle("active", vEl.id === "view-" + v));
    currentView = v;
    loadView(v);
    history.replaceState(null, "", "#" + v);
  });
});

// hash routing on initial load
(function(){
  const h = location.hash.slice(1);
  if(h){ const el = document.querySelector(`.nav-item[data-view="${h}"]`); if(el) el.click(); }
})();

// ── View dispatch ──
function loadView(v){
  if(v === "home")      return loadHome();
  if(v === "reminders") return loadReminders();
  if(v === "todos")     return loadTodos();
  if(v === "money")     return loadMoney();
  if(v === "insights")  return loadInsights();
}

// ── Shared renderers ──
function renderMoneyBars(earnBarId, spentBarId, earnAmtId, spentAmtId, earned, spent){
  const mx = Math.max(earned, spent, 1);
  document.getElementById(earnBarId).style.width  = (earned / mx * 100) + "%";
  document.getElementById(spentBarId).style.width = (spent  / mx * 100) + "%";
  document.getElementById(earnAmtId).textContent  = fmt(earned);
  document.getElementById(spentAmtId).textContent = fmt(spent);
}

function renderReminders(data, listId, countId){
  if(countId) document.getElementById(countId).textContent = data.length ? data.length + " upcoming" : "";
  const el = document.getElementById(listId);
  if(!data.length){ el.innerHTML = '<div class="empty">No upcoming reminders</div>'; return; }
  el.innerHTML = data.map(r => {
    let badge = "";
    if(r.label === "Today")    badge = '<span class="badge today">today</span>';
    else if(r.label === "Tomorrow") badge = '<span class="badge tmrw">tmrw</span>';
    return `<div class="row">
      <div class="row-icon">🔔</div>
      <div class="row-text">
        <div class="row-main">${esc(r.text)}${badge}</div>
        <div class="row-sub">${esc(r.label)}</div>
      </div>
    </div>`;
  }).join("");
}

function renderTodos(data, listId, countId){
  if(countId) document.getElementById(countId).textContent = data.length ? data.length + " open" : "";
  const el = document.getElementById(listId);
  if(!data.length){ el.innerHTML = '<div class="empty">All clear — no open todos</div>'; return; }
  el.innerHTML = data.map(t => `<div class="row">
    <div class="row-icon" style="color:var(--muted)">☐</div>
    <div class="row-text">
      <div class="row-main">${esc(t.text)}</div>
      ${t.due ? `<div class="row-sub">Due ${esc(t.due)}</div>` : ""}
    </div>
  </div>`).join("");
}

function renderProfile(obs, listId, countId){
  if(countId) document.getElementById(countId).textContent = obs.length ? obs.length + " observations" : "";
  const el = document.getElementById(listId);
  if(!obs.length){
    el.innerHTML = '<div class="empty">No profile data yet — speak to Nova for a week, then say "run reflection"</div>';
    return;
  }
  el.innerHTML = obs.map(o => {
    const cls  = CAT_CLASS[o.category] || "cat-general";
    const pct  = Math.round((o.confidence || 0.7) * 100);
    return `<div class="obs-row">
      <div class="obs-meta">
        <span class="cat-tag ${cls}">${esc(o.category)}</span>
        <div class="conf-bar"><div class="conf-fill" style="width:${pct}%"></div></div>
      </div>
      <div class="row-text"><div class="row-main" style="white-space:normal;line-height:1.5">${esc(o.observation)}</div></div>
    </div>`;
  }).join("");
}

// ── Home ──
async function loadHome(){
  const [d, cal, prof] = await Promise.all([
    fetch("/api/data").then(r=>r.json()).catch(()=>null),
    fetch("/api/calendar").then(r=>r.json()).catch(()=>({events:[], unavailable:true})),
    fetch("/api/profile").then(r=>r.json()).catch(()=>({observations:[]})),
  ]);
  if(!d) return;

  document.getElementById("ts").textContent = d.ts;

  // Metric cards
  const s = d.summary;
  document.getElementById("m-rem").textContent    = s.reminder_count;
  document.getElementById("m-tasks").textContent  = s.task_count;
  document.getElementById("m-earned").textContent = fmt(s.earned_month);
  document.getElementById("m-spent").textContent  = fmt(s.spent_month);

  // Money bars
  renderMoneyBars("hbar-earned","hbar-spent","hbar-earned-amt","hbar-spent-amt", s.earned_month, s.spent_month);

  // Today strip
  const strip = document.getElementById("today-strip");
  const cnt   = document.getElementById("today-count");
  if(cal.unavailable){
    strip.innerHTML = '<span style="color:var(--muted);font-size:13px">Calendar not available — check Calendar permissions in System Settings</span>';
    cnt.textContent = "";
  } else if(!cal.events || !cal.events.length){
    strip.innerHTML = '<span style="color:var(--muted);font-size:13px">Nothing on the calendar today</span>';
    cnt.textContent = "";
  } else {
    cnt.textContent = cal.events.length + " event" + (cal.events.length !== 1 ? "s" : "");
    strip.innerHTML = cal.events.map(e => `<div class="event-chip">
      <div class="event-chip-title">${esc(e.title)}</div>
      <div class="event-chip-time">${esc(e.time)}</div>
    </div>`).join("");
  }

  // Reminders (first 5 on home overview)
  renderReminders(d.reminders.slice(0,5), "h-rem-list", "h-rem-count");

  // Todos (first 5 on home overview)
  renderTodos(d.todos.slice(0,5), "h-todo-list", "h-todo-count");

  // Profile
  renderProfile(prof.observations || [], "h-profile-list", "h-profile-count");

  // Activity feed
  const feed = document.getElementById("feed-list");
  if(!d.feed.length){ feed.innerHTML = '<div class="empty">No activity yet — speak to Nova first</div>'; }
  else {
    feed.innerHTML = d.feed.map(e => `<div class="row">
      <div class="row-icon kind-${esc(e.kind)}">${KIND_ICONS[e.kind] || "·"}</div>
      <div class="row-text">
        <div class="row-main">${esc(e.label)}</div>
        <div class="row-sub">${esc(e.ago)}</div>
      </div>
    </div>`).join("");
  }
}

// ── Reminders view ──
async function loadReminders(){
  const d = await fetch("/api/data").then(r=>r.json()).catch(()=>null);
  if(!d) return;
  renderReminders(d.reminders, "rem-view-list", "rem-view-count");
}

// ── Todos view ──
async function loadTodos(){
  const d = await fetch("/api/data").then(r=>r.json()).catch(()=>null);
  if(!d) return;
  renderTodos(d.todos, "todo-view-list", "todo-view-count");
}

// ── Money view ──
async function loadMoney(){
  const d = await fetch("/api/money").then(r=>r.json()).catch(()=>null);
  if(!d) return;
  renderMoneyBars("mbar-earned","mbar-spent","mbar-earned-amt","mbar-spent-amt", d.earned_month, d.spent_month);
  const el = document.getElementById("money-tx-list");
  if(!d.transactions.length){ el.innerHTML = '<div class="empty">No transactions yet</div>'; return; }
  el.innerHTML = d.transactions.map(t => {
    const arrow = t.type === "earned" ? "↑" : "↓";
    const label = t.note || (t.type === "earned" ? "Earned" : "Spent");
    return `<div class="tx-row">
      <div class="tx-arrow kind-money">${arrow}</div>
      <div class="tx-note">${esc(label)}</div>
      <div class="tx-ago">${esc(t.ago)}</div>
      <div class="tx-amount ${esc(t.type)}">${fmt(t.amount)}</div>
    </div>`;
  }).join("");
}

// ── Insights view ──
async function loadInsights(){
  const prof = await fetch("/api/profile").then(r=>r.json()).catch(()=>({observations:[]}));
  renderProfile(prof.observations || [], "ins-profile-list", "ins-profile-count");
}

// ── Auto-refresh every 15s ──
setInterval(() => loadView(currentView), 15000);

// Initial load
loadView("home");
</script>

</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return _HTML


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
