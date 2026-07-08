# Agent Configuration UI — Plan

## Goal
Add a `/api/agent/config` backend router and an `AgentConfigPanel.vue` frontend component so users can configure the agent loop (LLM URL, model, max rounds, workspace, system prompt append) via the UI instead of env vars.

## User decisions
- API key: NEVER returned in GET (write-only, most secure)
- system_prompt_append: YES include textarea in the form

## Success criteria
- GET /api/agent/config returns config without api_key field
- PUT /api/agent/config persists to data/agent_config.json
- DELETE /api/agent/config resets to env defaults
- AgentConfigPanel renders in agents.vue, shows config, has edit modal + reset
- Chat router uses persisted config immediately after save
- No existing functionality broken

## Current context
- `backend/services/agent/llm.py` — AgentSettings.from_env() reads env vars
- `backend/routers/chat.py` — uses AgentSettings.from_env() directly
- `backend/main.py` — registers routers
- `frontend/app/pages/agents.vue` — static mock data, no real backend calls
- `frontend/app/composables/useApi.ts` — api namespaces per feature
- `frontend/app/components/mcp/McpManager.vue` — reference pattern for full CRUD component

## Risk: medium
Blast radius: backend (3 files + 1 new), frontend (3 files + 1 new)

## Mode: delegated
Two independent write packets (backend / frontend) can be parallelised.

## Work packets
- P1 (backend): new router + model + llm.py update + main.py + chat.py
- P2 (frontend): new component + agents.vue update + useApi.ts update

## Eval contract (inline)
- Outcome: full agent config read/write UI wired to backend
- Shared surfaces: useApi.agentConfig ↔ GET/PUT/DELETE /api/agent/config
- Required checks: backend starts without error, frontend page loads
- Blocking conditions: P2 depends on knowing the API shape from P1
- Handoff evidence: P1 declares final field names; P2 uses those exact names

## Integration policy
Parent integrates after both packets complete. Checks field name consistency.

## Verification
- Start FastAPI, hit GET /api/agent/config, confirm no api_key in response
- Load /agents page, confirm panel renders, edit modal opens, save works
