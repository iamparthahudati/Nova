# Nova Backend

Backend runtime code lives in `apps/backend`:

- `memory/` (only persistence owner)
- `domains/` (Finance, WorkOS — business rules, no I/O)
- `services/` (domain services, including Brain as Claude owner)
- `money.py` (shared `MoneyAmount` — Finance and WorkOS both import this)
- `nova.py` (assistant composition root)
- `dashboard.py` (read-only web dashboard)
- `tests/`

## WorkOS governance

WorkOS implementation follows frozen ADRs 0021–0023 and
[`docs/workos/IMPLEMENTATION_GOVERNANCE.md`](../../docs/workos/IMPLEMENTATION_GOVERNANCE.md).
Every WorkOS PR must pass:

- `tests/architecture/test_dependencies.py` — `domains.work` may import only
  `{memory, runtime}` plus root utils; `services.planner` and `services.api`
  may import `domains.work`.
- `tests/architecture/test_workos_governance.py` — no derived columns in
  migrations; `MutationEvent` shape unchanged; entity_type vocabulary registered.
- Real SQLite tests — never mock the database.

Build order: [`docs/workos/IMPLEMENTATION_PLAN.md`](../../docs/workos/IMPLEMENTATION_PLAN.md).

## Run

```bash
cd apps/backend
python nova.py
```

Dashboard:

```bash
cd apps/backend
uvicorn dashboard:app --port 8000
```

API facade (Milestone 2.11 — for Electron, CLI, future clients):

```bash
cd apps/backend
uvicorn api_server:app --port 8001
# or: python api_server.py
```

Endpoints: `GET /health`, `POST /chat`, read routes under `/tasks`, `/calendar`, `/reminders`, `/memory`, `/graph`, `/spending`, `/products`, `/settings`. WebSockets: `/ws/chat`, `/ws/events`.

## Storage and repo paths

Persistent data is resolved via `paths.py` and defaults to repo-root `data/`:

- `data/nova.db`
- `data/nova_lancedb/`

Other repo-root paths (defined in `paths.py`, not yet wired into services):

| Constant | Default location |
|----------|------------------|
| `DATA_ROOT` | `data/` |
| `ASSETS_ROOT` | `assets/` |
| `CONFIG_ROOT` | `config/` |
| `MODELS_ROOT` | `models/` |

Shared assets: `assets/images/`, `assets/audio/`, `assets/fonts/`.
Future local model weights: `models/embeddings/`, `models/whisper/`, `models/vision/`.
