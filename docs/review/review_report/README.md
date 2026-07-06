# RAI — Milestone Review Report

**Generated:** 2026-07-01
**Roadmap source:** [`Rai-ROADMAP-4.md`](../Rai-ROADMAP-4.md) ("Architecture First")
**Branch:** `phase-7-calendar` (legacy phase numbering from `RAI-ROADMAP-3.md` / `RAI_ROADMAP.md` — see note below)
**Base commit:** `b0d26e4` — "feat: Rai phases 0–5 complete" (only commit on this branch; everything else is uncommitted working-tree state)

---

## ⚠️ Naming collision worth flagging

The branch name `phase-7-calendar` and the in-code comments (`# --- Phase 7: Calendar & reminders ---`, `# --- Phase 11: ...`, `# --- Phase 13: ...`) refer to the **old, feature-numbered roadmap** (`RAI_ROADMAP.md` / `RAI-ROADMAP-2.md` / `RAI-ROADMAP-3.md`), where "Phase 7" = calendar & reminders as a *feature*.

`Rai-ROADMAP-4.md` supersedes that scheme with an **architecture-first** plan: Phase 1 has 8 *milestones* (Memory, Voice, Brain, Planner, Calendar, Automation, Knowledge, Bootstrap), each meaning "extract this concern into its own service." This report is scoped to **Roadmap v4**, since that is the roadmap file you asked me to analyze. Don't confuse "Milestone 5 — Calendar Service" (v4, not started) with the old "Phase 7 — Calendar" (feature, already working, just not yet extracted).

---

## Where we are right now

RAI v4 is in **Phase 1 — Architecture Foundation**. Of the 8 milestones required to close Phase 1, **3 are done** (Memory, Voice, Brain) and **5 remain**, all reflecting logic that currently still lives inline in `nova.py` / `dashboard.py`:

| # | Milestone | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Memory Service | ✅ Done | `memory/` package, repository-pattern-ish, sole owner of `nova.db` |
| 2 | Voice Service | ✅ Done | `services/voice/` package, no audio logic left in `nova.py` |
| 3 | Brain Service | ✅ Done | `services/brain/` package, owns Claude API + tool routing |
| 4 | Planner Service | ❌ Not started | briefing/wrap-up/pomodoro/`read_my_day` logic still in `nova.py` |
| 5 | Calendar Service | ❌ Not started | AppleScript calendar code still in `nova.py`, **duplicated** in `dashboard.py` |
| 6 | Automation Service | ❌ Not started | WhatsApp + `open_app`/`COMMANDS` AppleScript still in `nova.py` |
| 7 | Knowledge Service | ❌ Not started | weather/GitHub/RSS providers still in `nova.py` |
| 8 | Bootstrap | ❌ Not started | `nova.py` is 1,095 lines vs. the <100-line target |

**Phase 1 completion: 3 / 8 milestones = 37.5%.**
Phases 2–6 (Semantic Memory, Knowledge Engine, Developer Service, Vision, Desktop) cannot start until Phase 1 closes, and no work has begun on any of them — **0%** each.

Weighting all 8 Phase-1 milestones + 5 later phases equally as "13 units of roadmap," current overall progress is **~23%** of Phase 1's gate and **~6%** of the full v4 roadmap by unit count. Take the percentage as a rough size signal, not a precise metric — the remaining Phase 1 milestones (Bootstrap especially) are entangled and will not all take equal effort.

---

## Reports in this folder

| File | Covers |
|---|---|
| [phase-1-architecture-foundation.md](phase-1-architecture-foundation.md) | Milestones 1–8, in depth — this is where all the real content is |
| [phase-2-semantic-memory.md](phase-2-semantic-memory.md) | Not started |
| [phase-3-knowledge-engine.md](phase-3-knowledge-engine.md) | Not started |
| [phase-4-developer-service.md](phase-4-developer-service.md) | Not started |
| [phase-5-vision.md](phase-5-vision.md) | Not started |
| [phase-6-desktop.md](phase-6-desktop.md) | Not started |

---

## Top-line known issues (see phase-1 report for detail)

1. **Duplicated logic** — `dashboard.py` re-implements macOS Calendar fetching via its own `osascript` call instead of reusing `nova.py`'s `get_events()`. Directly violates Roadmap v4's "No duplicated logic" rule, and will get worse once a Calendar service exists and dashboard doesn't use it.
2. **`nova.py` still owns 5 unextracted concerns** (Calendar, Automation, Knowledge, Planner logic, plus all tool-handler wiring) — it grew from 850 net new lines in this diff alone, moving further from the <100-line Bootstrap target rather than closer to it.
3. **No tests** exist anywhere in the repo (`memory/`, `services/`, `nova.py`, `dashboard.py`) despite "Unit-testable" and "Tests" being explicit Definition-of-Done / Milestone-1 requirements.
4. **No `RaiApplication` class or `services/__init__.py` re-exports** — `services/__init__.py` is empty, so `from services import *` (the target `nova.py` shape from the roadmap) would currently import nothing.
