# Nagare

Two independent apps. Run commands from their package roots, not repository root.

## Commands

### Backend (`backend/`)

- Run API: `uvicorn main:app --reload --port 8000`.
- Run full suite: `python -m pytest -q`; focused: `python -m pytest tests/test_models.py::test_model_crud_when_model_exists -q`.
- Tests import top-level `routers` and `services`, so run them from `backend/`.
- `requirements.txt` is runtime-only; install pytest and AnyIO test support separately in a host-native environment before running tests. Checked-in `.venv` targets Windows and is not portable to Linux.
- Tests mock LLMs and isolate SQLite/MCP config with temporary paths. Keep new tests off `backend/data/`, which is tracked runtime state.

### Frontend (`frontend/`)

- Use pinned `pnpm@11.9.0`, never npm. CI uses Node 22.
- Install first: `pnpm install`; its `postinstall` runs `nuxt prepare` and generates required Nuxt artifacts.
- Verify in CI order: `pnpm lint && pnpm typecheck`. `pnpm build` is production validation.
- No frontend test runner exists. CI lives at `frontend/.github/workflows/ci.yml`; no root/backend CI exists.
- `pnpm-workspace.yaml` patches `estree-walker` and blocks native build scripts. Preserve it and `patches/` when dependency changes touch lockfiles.

## Architecture

- `backend/main.py` is ASGI composition root. It creates one `SessionManager` and injects it into `sessions`, `history`, and `chat` via `_register()`; session-aware routers need matching startup wiring or return `503`.
- Backend persistence is SQLite in `backend/data/app.db`. `connect_db()` enables foreign keys and runs idempotent schema upgrades on every connection; no migration command exists.
- `backend/data/agent_config.json` overrides environment LLM settings for every stream. Agent memory, skills, MCP config, and runtime DB state also live under `backend/data/`.
- Chat `POST /api/chat/stream` is SSE, not JSON request/response. Preserve `delta`, `replace_last`, tool, error, and done event handling. Session mode `chat` disables tools; agent mode may execute XML tool calls in configured workspace.
- Frontend `/api/**` normally stays relative and Nuxt proxies it to `http://localhost:8000/api/**` so auth cookies and CSRF work. Setting `NUXT_PUBLIC_API_BASE` bypasses that default browser path.
- Root `app.vue` installs auth middleware globally. Authenticated browser requests include cookies; mutations require `X-CSRF-Token` from `csrf_token` cookie.
- `useApi()` is legacy convenience barrel. New frontend code should import specific domain composables from `app/composables/useApi/`.

## Runtime Checks

- Default agent LLM endpoint is OpenAI-compatible `http://localhost:11434/v1`; use mocks for tests. Knowledge ingestion initializes persistent Chroma/FastEmbed storage, so skip it in quick checks.
- Backend CORS permits only `http://localhost:3000`; changing frontend dev port needs matching backend config.
- Treat `backend/data/` as mutable tracked application state. Avoid manual edits or destructive test/server runs against it.

## Local Artifacts

- Do not treat `.omc/`, `.omo/`, `.workflow/`, `.serena/`, `.codegraph/`, or `graphify-out/` as product sources or durable project guidance. They are local tool state/generated output.
- `ROADMAP.md` and `progress.txt` are ignored local planning files; do not rely on them as current implementation contracts.
