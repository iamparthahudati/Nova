# Nova Desktop

Electron + React shell for Nova. The renderer reads live data from the FastAPI facade (`services/api`) over HTTP, with optional mock mode for UI-only development. See [`docs/architecture/ARCHITECTURE_v2.md`](../../docs/architecture/ARCHITECTURE_v2.md).

## Stack

| Layer | Technology |
|-------|------------|
| Renderer | React 19, React Router (hash), TanStack Query, Zustand, Tailwind CSS 4, shadcn/ui |
| Contracts | `@nova/api-contracts` (shared types with backend) |
| Build / dev | Vite 8, `vite-plugin-electron@^1.1.0` |
| Main / preload | TypeScript, Electron 43 |
| Lint | Oxlint |

## Data flow

```
Screen → hook (useQuery) → data-source → nova-api → FastAPI
                              ↓ (VITE_USE_MOCKS=true)
                         dev/mocks/api
```

- **Live mode:** HTTP GET to `VITE_NOVA_API_URL` (default `http://localhost:8001`)
- **Mock mode:** `VITE_USE_MOCKS=true` — no backend HTTP, no WebSocket
- **WebSocket:** `/ws/events` for React Query cache invalidation only (live mode)
- **Chat:** UI placeholder only — backend integration deferred

Types flow through `@nova/api-contracts` → mappers → view models → components. Screens never import backend Python or touch SQLite/LanceDB.

## Project layout

```
apps/desktop/
├── electron/
│   ├── main.ts       # Main process (windows, IPC)
│   └── preload.ts    # contextBridge → window.desktopWindow
├── src/
│   ├── services/     # data-source, nova-api
│   ├── hooks/        # React Query hooks per domain
│   ├── mappers/      # api-contracts → view models
│   ├── view-models/  # camelCase types for components
│   ├── query/        # QueryClient + query key registry
│   ├── websocket/    # /ws/events invalidation
│   └── dev/mocks/    # Mock data (VITE_USE_MOCKS only)
├── dist/             # Built renderer (production)
├── dist-electron/    # Built main.js + preload.mjs (gitignored)
├── index.html
└── vite.config.ts
```

## Requirements

- macOS (primary target for window chrome)
- Node.js ≥ 22
- npm

## Setup

```bash
cd apps/desktop
npm install
```

On first install, the Electron binary is downloaded by the `electron` package postinstall.

## Development

### Live backend

Terminal 1 — API server:

```bash
cd apps/backend
python3 api_server.py
```

Terminal 2 — desktop:

```bash
cd apps/desktop
npm run dev
```

Optional env (defaults shown):

```bash
VITE_NOVA_API_URL=http://localhost:8001 npm run dev
```

### Mock mode (no backend)

```bash
VITE_USE_MOCKS=true npm run dev
```

### Unified dev workflow

```bash
npm run dev
```

- Renderer: Vite HMR at `http://localhost:5173/` (`strictPort: true`)
- Main process: hot restart on `electron/main.ts` changes
- Preload: rebuild + renderer reload on `electron/preload.ts` changes
- Dev server URL: set automatically as `process.env.VITE_DEV_SERVER_URL` by `vite-plugin-electron` (do not set manually)

### Clean dev (no stale artifacts)

```bash
rm -rf dist dist-electron node_modules/.vite
npm run dev
```

### Port conflicts

Dev uses port **5173** with `strictPort: true`. If the port is in use, free it or change `server.port` in `vite.config.ts`.

## Production build

```bash
npm run build    # tsc -b (typecheck) + vite build
npm run start    # electron . (production bundle)
```

Output:

- `dist/` — renderer (`index.html`, assets)
- `dist-electron/main.js` — main process entry (`package.json` `"main"`)
- `dist-electron/preload.mjs` — preload script

If `electron .` fails with missing `BrowserWindow` exports, ensure `ELECTRON_RUN_AS_NODE` is not set in your shell. The `start` script unsets it automatically.

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Unified Vite + Electron development |
| `npm run build` | Typecheck renderer + production build (renderer + main + preload) |
| `npm run start` | Run packaged build via `electron .` |
| `npm run typecheck:electron` | Type-check main/preload only (`tsconfig.electron.json`, no emit) |
| `npm run lint` | Oxlint |

## Preload API

The preload script exposes a small window API used by the custom title bar:

```ts
window.desktopWindow?.minimize()
window.desktopWindow?.maximize()
window.desktopWindow?.close()
```

IPC channels in main: `window:minimize`, `window:maximize`, `window:close`.

## TypeScript

| Config | Purpose |
|--------|---------|
| `tsconfig.app.json` | Renderer (`src/`) |
| `tsconfig.electron.json` | Main/preload type-check only (`noEmit: true`) |
| `tsconfig.node.json` | Vite config |

`npm run build` runs `tsc -b`, which type-checks all referenced projects including electron.

## Future monorepo dev

`concurrently` is kept as a dependency for a planned workflow that will start the backend, API server, and Electron together. That wiring is not implemented yet.

## Architecture boundary

The desktop app is a **leaf consumer**. It must not import Python or backend modules directly. All Nova data goes through `services/api` over HTTP/WebSocket. Brain, Memory, and `runtime/conversation` remain backend-only concerns.
