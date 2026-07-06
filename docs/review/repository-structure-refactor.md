# Repository Structure Refactor — Migration Report

**Date:** 2026-07-05  
**Scope:** Path-only repository hygiene; no business logic, API, or runtime behavior changes.

---

## 1. Summary

Reorganized the Nova monorepo toward the 5-year target layout: nested `assets/`, categorized `scripts/`, new `config/` and `models/` placeholders, shared `packages/` scaffolding, extended `paths.py` constants, and documentation path updates. All 25 backend unit tests pass; desktop lint and build succeed.

**Architecture score:** 8 / 10 (up from 6.5 / 10)

---

## 2. Moved files

| From | To |
|------|-----|
| `assets/icons/` | `assets/images/icons/` |
| `assets/logos/` | `assets/images/logos/` |
| `assets/wallpapers/` | `assets/images/wallpapers/` |
| `assets/sounds/` | `assets/audio/notification/` |
| `scripts/setup.py` | `scripts/dev/setup.py` |
| `scripts/migrate.py` | `scripts/database/migrate.py` |
| `scripts/backup.py` | `scripts/database/backup.py` |
| `scripts/release.py` | `scripts/release/release.py` |

---

## 3. Updated imports

**None.** No Python or TypeScript module paths changed. Backend continues to use flat imports from `apps/backend/`.

---

## 4. Updated filesystem paths

| File | Change |
|------|--------|
| `apps/backend/paths.py` | Added `ASSETS_ROOT`, `CONFIG_ROOT`, `MODELS_ROOT` |
| `apps/backend/requirements.txt` | Added explicit `pyarrow` (already used transitively) |
| `.gitignore` | Ignore `models/**/*` except `.gitkeep` |
| `.env.example` | Commented future asset/model path examples |
| `README.md` | Added repository layout section |
| `apps/backend/README.md` | Documented path constants and folder layout |
| `docs/architecture/ARCHITECTURE_v1.md` | Monorepo path note |
| `docs/architecture/ARCHITECTURE_v2.md` | Monorepo path note |
| `docs/architecture/AI_CONTRACTS.md` | Monorepo path note + `apps/backend/` link prefixes |

---

## 5. Placeholders added

### Config
- `config/prompts/.gitkeep`
- `config/personas/.gitkeep`
- `config/templates/.gitkeep`
- `config/themes/.gitkeep`
- `config/README.md`

### Models
- `models/embeddings/.gitkeep`
- `models/whisper/.gitkeep`
- `models/vision/.gitkeep`

### Assets
- `assets/audio/wakewords/.gitkeep`
- `assets/audio/voices/.gitkeep`

### Packages
- `packages/shared-types/package.json` + `README.md`
- `packages/api-contracts/package.json` + `README.md`
- `packages/ui/package.json` + `README.md`
- `packages/utils/package.json` + `README.md`

### Scripts
- `scripts/database/README.md`
- `scripts/dev/README.md`
- `scripts/release/README.md`

---

## 6. Breaking changes

**None for runtime.** No code referenced old asset or script paths.

**User-managed:** LaunchAgent plist absolute paths (documented in README) are outside the repo and unchanged.

---

## 7. Backend verification

```
cd apps/backend && .venv/bin/python -m unittest discover tests -v
→ Ran 25 tests in 0.003s — OK
```

Path smoke test:
```
REPO_ROOT  → /Users/parthahudati/nova
DATA_ROOT  → /Users/parthahudati/nova/data
ASSETS_ROOT → /Users/parthahudati/nova/assets
CONFIG_ROOT → /Users/parthahudati/nova/config
MODELS_ROOT → /Users/parthahudati/nova/models
```

---

## 8. Desktop verification

```
cd apps/desktop && npm run lint && npm run build
→ lint: 2 pre-existing warnings (only-export-components)
→ build: tsc -b + vite build (renderer + main + preload via vite-plugin-electron) — success
```

Development workflow: `npm run dev` (unified Vite + Electron via `vite-plugin-electron`). See [`apps/desktop/README.md`](../../apps/desktop/README.md).

---

## 9. Test verification

25 / 25 tests passed (context engine + context providers).

---

## 10. Remaining technical debt

1. Flat Python imports require `cd apps/backend`
2. No `pyproject.toml` / installable package
3. Root README body still describes Phase-0 Porcupine prototype
4. Architecture/review docs use flat `rai/` paths in body text
5. Empty `services/__init__.py` — bootstrap target not met
6. `nova.py` at 333 lines vs documented `<100` target
7. `dashboard.py` duplicate calendar AppleScript
8. Embedding cache still at `~/.cache/rai/fastembed`
9. No npm workspace wiring for `packages/`
10. `requirements/` split deferred — single `apps/backend/requirements.txt` retained

---

## 11. Requirements decision

**Kept** `apps/backend/requirements.txt` as the single canonical file. Splitting into `requirements/{backend,dev,test}.txt` would produce empty dev/test files with no CI benefit today.

---

## 12. Recommendations before API milestone

1. Add `pyproject.toml` for installable `nova-backend`
2. Wire npm/pnpm workspaces when desktop replaces mocks
3. Implement `services/api/` per ARCHITECTURE_v2 Milestone 2.11
4. Implement `scripts/database/migrate.py` before schema churn
5. Fix dashboard calendar to call `calendar.get_events()`
6. Refresh or archive stale review reports (2026-07-01)
7. Rename embedding cache `rai` → `nova` in a dedicated milestone
