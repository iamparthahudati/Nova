# Nova Backend

Backend runtime code lives in `apps/backend`:

- `memory/` (only persistence owner)
- `services/` (domain services, including Brain as Claude owner)
- `nova.py` (assistant composition root)
- `dashboard.py` (read-only web dashboard)
- `tests/`

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
