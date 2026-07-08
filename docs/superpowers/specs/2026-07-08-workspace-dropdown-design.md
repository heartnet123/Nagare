# Workspace Dropdown with Model and Agent Selector

Implement a dynamic tabbed workspace dropdown in the dashboard header to select default LLM models and custom agents for new chat sessions.

## Goals
- Replace the static "Default Workspace" button in the dashboard layout header with a dynamic dropdown.
- Fetch real models from the backend via a new endpoint `/api/models` (connected to the configured LLM provider).
- Fetch agents from the existing `/api/agents` endpoint.
- Provide a tabbed UI (Models and Agents tabs) to switch and select workspace settings.
- Show a call-to-action "Create your own agent in Agent page" under the Agents tab if no agents exist.
- Persist the selected workspace to `localStorage`.
- Apply the selection as the default configuration when launching new chat sessions.

---

## Technical Specifications

### 1. Backend Changes

#### 1.1 New Models Router
- **File**: `backend/routers/models.py` [NEW]
- **Endpoint**: `GET /api/models`
- **Logic**:
  - Load LLM settings using `AgentSettings.from_config_file()`.
  - Send a `GET` request to `{base_url}/models` with the `Authorization` header (`Bearer {api_key}`).
  - If successful, parse OpenAI-compatible response and return a list of model strings (e.g. `["llama3.1", "gpt-4o"]`).
  - Fall back to a curated static list if the connection fails or Ollama/OpenAI is offline:
    ```python
    ["llama3.1", "llama3", "gpt-4o", "gpt-3.5-turbo", "claude-3-5-sonnet", "mistral"]
    ```
- **Registration**: Include in `backend/main.py`.

#### 1.2 Chat Router Update
- **File**: `backend/routers/chat.py` [MODIFY]
- **Payload changes**: Add `model` and `agent_id` optional fields to `ChatStreamRequest`.
- **Stream resolution**:
  - In `event_stream(payload)`:
    - If `payload.agent_id` is supplied, load the agent config from `backend/data/agents.json`.
    - Set the chat session model to the agent's model (if not overridden by `payload.model`).
    - Resolve the agent's system prompt and pass it to `stream_agent`.
- **File**: `backend/services/agent/loop.py` [MODIFY]
  - Add optional `agent_system_prompt` argument to `stream_agent(messages, settings, agent_system_prompt: str | None = None)`.
  - Prepend/append the agent's prompt to `_system_prompt_append`.

---

### 2. Frontend Changes

#### 2.1 API Composable
- **File**: `frontend/app/composables/useApi/models.ts` [NEW]
  - Expose `list()` method to query `/api/models`.
- **File**: `frontend/app/composables/useApi/index.ts` [MODIFY]
  - Register and export `useApiModels()`.

#### 2.2 Workspace Selection Store
- **File**: `frontend/app/composables/useWorkspaceStore.ts` [NEW]
  - Define `selectedWorkspace` state:
    ```typescript
    interface SelectedWorkspace {
      type: 'default' | 'model' | 'agent'
      id: string
      name: string
    }
    ```
  - On mount, initialize from `localStorage` if exists, defaulting to:
    ```typescript
    { type: 'default', id: 'default', name: 'Default Workspace' }
    ```
  - Fetch models and agents from backend concurrently.
  - Expose `selectedLabel` computed property:
    - If type is `'default'`: `"Default Workspace"`
    - If type is `'model'`: `"Model: " + name`
    - If type is `'agent'`: `"Agent: " + name`

#### 2.3 UI Components
- **File**: `frontend/app/components/layout/WorkspaceDropdown.vue` [NEW]
  - Render trigger button showing `selectedLabel` (no icon prefix, keep `ChevronDown` arrow).
  - Open popup containing:
    - Tab bar ("Models" and "Agents") with animated slide highlights.
    - Curated model list with checkmark indicators.
    - Agent list. If empty, show centered empty state card: "Create your own agent in Agent page" pointing to `/agents`.
- **File**: `frontend/app/layouts/default.vue` [MODIFY]
  - Replace the static "Default Workspace" button with the `<LayoutWorkspaceDropdown />` component.

#### 2.4 Chat Integration
- **File**: `frontend/app/components/chat/ChatView.vue` [MODIFY]
- **File**: `frontend/app/pages/session/[id].vue` [MODIFY]
- **File**: `frontend/app/composables/useChatSession.ts` [MODIFY]
  - When initiating a new chat stream, read `selectedWorkspace` from `useWorkspaceStore`.
  - Pass the respective `model` or `agent_id` parameter to `/api/chat/stream`.

---

## Verification Plan

### Automated Tests
- Run backend lint and basic router test validation to confirm API health.

### Manual Verification
- Click Workspace dropdown in dashboard header and verify that tabs can be switched and values populate correctly.
- Select a model and verify dropdown button header updates to `"Model: [name]"`.
- Select an agent and verify dropdown button header updates to `"Agent: [name]"`.
- Clear any agents and verify agents tab displays "Create your own agent in Agent page" linking to the agents page.
- Select a model/agent, open a new chat session, and verify from backend log files (or network panel requests) that the selected model or agent settings are passed to `/api/chat/stream`.
