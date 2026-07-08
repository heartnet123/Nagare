# Homepage Mode Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Chat / Agent" mode switcher to the homepage chat input that preserves user selection across the session.

**Architecture:** We use Nuxt's `useState` for session-persistent state and modify the `/api/session` payload to include the selected mode.

**Tech Stack:** Vue 3, Nuxt 3, Tailwind CSS, Lucide Icons

## Global Constraints

- Must keep existing chat input functionality working without regression
- Must preserve mode during current session
- Disable switching while creating
- Include `{ "mode": "chat" | "agent" }` in the POST payload

---

### Task 1: Update Homepage Composer Component

**Files:**
- Modify: `frontend/app/components/home/Composer.vue`

**Interfaces:**
- Consumes: User click events to toggle mode
- Produces: Includes `mode: mode.value` in the POST body to `/api/session`

- [ ] **Step 1: Add state to script setup**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from '#app'
import { Paperclip, ArrowUp, Loader2 } from '@lucide/vue'

const value = ref('')
const router = useRouter()
const creating = ref(false)
const mode = useState<'chat' | 'agent'>('composer-mode', () => 'chat')

const submit = async () => {
  const text = value.value.trim()
  if (!text || creating.value) return

  creating.value = true
  try {
    const config = useRuntimeConfig()
    // Create a new session via the backend API
    const session = await $fetch('/api/session', {
      method: 'POST',
      baseURL: config.public.apiBase,
      body: { 
        name: text.length > 48 ? `${text.slice(0, 45)}...` : text,
        mode: mode.value
      },
    }) as any

    // Redirect to the dedicated session page with the initial query
    router.push(`/session/${session.id}?q=${encodeURIComponent(text)}`)
  } catch {
    // Fallback: just go to home if session creation fails
    router.push('/')
  } finally {
    creating.value = false
    value.value = ''
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    if (e.isComposing || creating.value) return
    e.preventDefault()
    submit()
  }
}
</script>
```

- [ ] **Step 2: Add switcher UI to template**

Modify the `<template>` of `frontend/app/components/home/Composer.vue`. In the button row (`<div class="flex items-center justify-end px-4 py-3 gap-3 bg-white">`), insert the switcher at the beginning of the div and add `mr-auto` to push it to the left side of the row, while the other icons stay on the right.

```vue
      <div class="flex items-center justify-end px-4 py-3 gap-3 bg-white">
        <div class="mr-auto bg-stone-100 dark:bg-stone-800 rounded-lg p-1 flex items-center gap-1">
          <button
            class="px-3 py-1 text-sm font-medium rounded-md transition-all"
            :class="[
              mode === 'chat' 
                ? 'bg-white dark:bg-stone-700 shadow-sm text-stone-900 dark:text-stone-100' 
                : 'text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300',
              creating ? 'opacity-50 cursor-not-allowed' : ''
            ]"
            :disabled="creating"
            @click="mode = 'chat'"
            aria-label="Chat Mode"
          >
            Chat
          </button>
          <button
            class="px-3 py-1 text-sm font-medium rounded-md transition-all"
            :class="[
              mode === 'agent' 
                ? 'bg-white dark:bg-stone-700 shadow-sm text-stone-900 dark:text-stone-100' 
                : 'text-stone-500 dark:text-stone-400 hover:text-stone-700 dark:hover:text-stone-300',
              creating ? 'opacity-50 cursor-not-allowed' : ''
            ]"
            :disabled="creating"
            @click="mode = 'agent'"
            aria-label="Agent Mode"
          >
            Agent
          </button>
        </div>

        <button
          class="p-2 text-stone-400 hover:text-stone-600 transition-colors"
          aria-label="Attach file"
        >
```

- [ ] **Step 3: Test and verify**
Start the frontend development server (`cd frontend && pnpm run dev`). Verify that the mode switcher appears, correctly updates state, toggles classes, and disabling works during submit. Ensure the payload sends `mode: "chat"` or `mode: "agent"`.

- [ ] **Step 4: Commit**
```bash
git add frontend/app/components/home/Composer.vue
git commit -m "feat(ui): add chat/agent mode switcher to homepage composer"
```

### Task 2: Support Session Mode in Backend

**Files:**
- Modify: `backend/services/data.py`
- Modify: `backend/models/session.py`
- Modify: `backend/services/session_manager.py`
- Modify: `backend/routers/sessions.py`
- Modify: `backend/routers/chat.py`

**Interfaces:**
- Consumes: `mode` field from create session request and session DB
- Produces: Persists `mode` in SQLite and disables tools for `chat` mode in streaming endpoint

- [ ] **Step 1: Update DB Schema and migration in backend/services/data.py**
Add `mode text` to the `sessions` table in `SCHEMA` and update `init_db` to perform the alter table migration if the `mode` column is missing.

- [ ] **Step 2: Update models in backend/models/session.py**
Add `mode: Optional[str] = "chat"` to `SessionCreateRequest`.

- [ ] **Step 3: Update session manager in backend/services/session_manager.py**
Update `create_session` signature to accept `mode: str = "chat"`, store it in the SQLite database column, and cache it. Update `_row_to_session_meta` (or database row mapping helper) to parse the `mode` column.

- [ ] **Step 4: Update routers in backend/routers/sessions.py**
Pass `body.mode` to `mgr.create_session` in `create_session` route.

- [ ] **Step 5: Disable tools for Chat mode in backend/routers/chat.py**
Check the session's mode in `event_stream`. If `session_mode == 'chat'`, set `settings.max_rounds = 1` (or construct stream agent without tool definitions in system prompt).

- [ ] **Step 6: Run tests and verify**
Run the backend tests to ensure everything builds and works properly.

- [ ] **Step 7: Commit**
```bash
git add backend/services/data.py backend/models/session.py backend/services/session_manager.py backend/routers/sessions.py backend/routers/chat.py
git commit -m "feat(backend): support session mode and disable tools for chat mode"
```
