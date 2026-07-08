<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import type { Session } from '~/types'
import { useRoute, useRouter } from 'vue-router'
import {
  Waves,
  ArrowUp,
  User,
  Wrench,
  Search,
  Trash2,
  Archive,
  Star,
  Plus,
  ChevronLeft,
  ChevronRight,
  ArchiveRestore,
  MessageSquare,
  Sparkles,
  X,
  AlertTriangle,
  ArrowDown
} from '@lucide/vue'

interface ToolEvent {
  id: string
  name: string
  input?: unknown
  output?: string
  error?: string
  status: 'running' | 'done' | 'error'
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  streaming?: boolean
  toolEvents?: ToolEvent[]
  metadata?: {
    input_tokens?: number
    output_tokens?: number
    response_time_ms?: number
  }
}

const props = withDefaults(defineProps<{
  isInDrawer?: boolean
}>(), {
  isInDrawer: false
})

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const api = useApi()
const sessionStore = useSessionStore()

// Shared Drawer states
const isChatDrawerOpen = sessionStore.chatDrawerOpen
const drawerSessionId = sessionStore.drawerSessionId

// Chat workspace state
const messages = ref<Message[]>([])
const busy = ref(false)
const scrollRef = ref<HTMLDivElement | null>(null)
const errorText = ref('')
const connectionError = ref(false)
const showScrollButton = ref(false)

// Abort controller to stop generation
let currentAbortController: AbortController | null = null

// Sessions list state
const sessionsList = sessionStore.sessions
const archivedSessionsList = ref<Session[]>([])
const currentSessionId = ref<string | null>(null)
const activeTab = ref<'active' | 'archived'>('active')
const searchQuery = ref('')
const sidebarCollapsed = ref(false)
const initialQuerySent = ref(false)

// Session inline edit state
const editingSessionId = ref<string | null>(null)
const editingName = ref('')
const renameInput = ref<HTMLInputElement[] | null>(null)

// Relative time formatter helper
const formatRelativeTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  try {
    const cleanStr = dateStr.replace(' ', 'T')
    const d = new Date(cleanStr)
    if (isNaN(d.getTime())) return dateStr
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

// Convert backend flat message array into nested UI Message structures
const formatHistoryMessages = (apiMessages: any[]): Message[] => {
  const formatted: Message[] = []
  let lastAssistant: Message | null = null

  for (const msg of apiMessages) {
    const isToolCall = msg.metadata?.source === 'tool' || msg.metadata?.tool_call || msg.metadata?.tool_result

    if (isToolCall) {
      const toolName = msg.metadata?.tool_call || msg.metadata?.tool_result || ''
      if (msg.role === 'assistant') {
        const event: ToolEvent = {
          id: msg.id,
          name: toolName,
          input: msg.metadata?.tool_input,
          status: 'done'
        }
        if (lastAssistant) {
          lastAssistant.toolEvents = lastAssistant.toolEvents || []
          lastAssistant.toolEvents.push(event)
        } else {
          lastAssistant = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: '',
            toolEvents: [event]
          }
          formatted.push(lastAssistant)
        }
      } else {
        if (lastAssistant && lastAssistant.toolEvents) {
          const event = lastAssistant.toolEvents.find(e => e.name === toolName && e.status === 'running')
            || [...lastAssistant.toolEvents].reverse().find(e => e.name === toolName)
          if (event) {
            event.output = msg.content.replace(/^.*?Tool result for `.*?`:_\n/, '')
            event.status = msg.metadata?.ok !== false ? 'done' : 'error'
          } else {
            lastAssistant.toolEvents.push({
              id: msg.id,
              name: toolName,
              output: msg.content,
              status: msg.metadata?.ok !== false ? 'done' : 'error'
            })
          }
        }
      }
    } else {
      const newMsg: Message = {
        id: msg.id,
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
        toolEvents: [],
        metadata: {
          input_tokens: msg.metadata?.input_tokens,
          output_tokens: msg.metadata?.output_tokens,
          response_time_ms: msg.metadata?.response_time_ms
        }
      }
      formatted.push(newMsg)
      if (msg.role === 'assistant') {
        lastAssistant = newMsg
      } else {
        lastAssistant = null
      }
    }
  }
  return formatted
}

// Fetch all active & archived sessions
const loadSessions = async () => {
  try {
    const searchVal = searchQuery.value.trim()
    const activeRes = await api.sessions.list(searchVal)
    const archivedRes = await api.sessions.listArchived(searchVal)
    sessionsList.value = activeRes.sessions
    archivedSessionsList.value = archivedRes.sessions
    if (!searchVal) {
      sessionStore.sessions.value = activeRes.sessions
    }
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

// Scroll to bottom helper
const scrollToBottom = () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTo({
        top: scrollRef.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

const handleScroll = () => {
  if (!scrollRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollRef.value
  showScrollButton.value = scrollHeight - scrollTop - clientHeight > 300
}

const forceScrollToBottom = () => {
  if (scrollRef.value) {
    scrollRef.value.scrollTo({
      top: scrollRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

// Watch query search to reload sessions
watch(searchQuery, () => {
  loadSessions()
})

const sessionIdToWatch = computed(() => {
  return props.isInDrawer ? drawerSessionId.value : (route.query.session as string | null)
})

// Sync active session based on URL route query or drawer session ID
watch(
  sessionIdToWatch,
  async (newVal) => {
    if (newVal) {
      currentSessionId.value = newVal
      try {
        const history = await api.sessions.getHistory(newVal)
        messages.value = formatHistoryMessages(history)
        scrollToBottom()
      } catch (err) {
        console.error('Failed to load session history:', err)
        errorText.value = 'Failed to load conversation history.'
      }
    } else {
      currentSessionId.value = null
      messages.value = []
      errorText.value = ''
    }
  },
  { immediate: true }
)

const currentSessionName = computed(() => {
  const current = sessionsList.value.find(s => s.id === currentSessionId.value)
    || archivedSessionsList.value.find(s => s.id === currentSessionId.value)
  return current ? current.name : 'New Chat'
})

const currentSessionModel = computed(() => {
  const current = sessionsList.value.find(s => s.id === currentSessionId.value)
    || archivedSessionsList.value.find(s => s.id === currentSessionId.value)
  return current ? current.model : null
})

// Route navigation actions / Drawer actions
const selectSession = (sid: string) => {
  if (props.isInDrawer) {
    drawerSessionId.value = sid
  } else {
    router.push({ query: { session: sid } })
  }
}

const startNewChat = () => {
  if (props.isInDrawer) {
    drawerSessionId.value = null
  } else {
    router.push('/')
  }
}

const createSessionForMessage = async (text: string) => {
  const name = text.length > 48 ? `${text.slice(0, 45)}...` : text
  const session = await api.sessions.create({ name })
  currentSessionId.value = session.id
  sessionsList.value = [session, ...sessionsList.value.filter((item) => item.id !== session.id)]
  sessionStore.sessions.value = sessionsList.value
  if (props.isInDrawer) {
    drawerSessionId.value = session.id
  }
  return session.id
}

// Session mutations
const deleteSession = async (sid: string) => {
  if (!confirm('Are you sure you want to permanently delete this conversation?')) return
  try {
    await api.sessions.delete(sid)
    if (currentSessionId.value === sid) {
      startNewChat()
    }
    await loadSessions()
  } catch (error) {
    console.error('Failed to delete session:', error)
  }
}

const archiveSession = async (sid: string) => {
  try {
    await api.sessions.archive(sid)
    if (currentSessionId.value === sid) {
      startNewChat()
    }
    await loadSessions()
  } catch (error) {
    console.error('Failed to archive session:', error)
  }
}

const unarchiveSession = async (sid: string) => {
  try {
    await api.sessions.unarchive(sid)
    await loadSessions()
    selectSession(sid)
  } catch (error) {
    console.error('Failed to unarchive session:', error)
  }
}

const toggleImportant = async (session: Session) => {
  try {
    await api.sessions.toggleImportant(session.id, !session.is_important)
    await loadSessions()
  } catch (error) {
    console.error('Failed to toggle important status:', error)
  }
}

const startRename = (sid: string, name: string) => {
  editingSessionId.value = sid
  editingName.value = name
  nextTick(() => {
    if (renameInput.value && renameInput.value[0]) {
      renameInput.value[0].focus()
      renameInput.value[0].select()
    }
  })
}

const saveRename = async (sid: string) => {
  if (!editingSessionId.value) return
  const finalName = editingName.value.trim()
  editingSessionId.value = null
  if (!finalName) return

  try {
    await api.sessions.update(sid, { name: finalName })
    await loadSessions()
  } catch (error) {
    console.error('Failed to rename session:', error)
  }
}

const updateAssistant = (id: string, patch: Partial<Message>) => {
  messages.value = messages.value.map((message) => message.id === id ? { ...message, ...patch } : message)
}

const addToolEvent = (assistantId: string, event: ToolEvent) => {
  messages.value = messages.value.map((message) => {
    if (message.id !== assistantId) return message
    return { ...message, toolEvents: [...(message.toolEvents || []), event] }
  })
}

const finishToolEvent = (assistantId: string, name: string, output: string, ok = true) => {
  messages.value = messages.value.map((message) => {
    if (message.id !== assistantId) return message
    const toolEvents = (message.toolEvents || []).map((event) => {
      if (event.name === name && event.status === 'running') {
        return { ...event, output, status: ok ? 'done' as const : 'error' as const }
      }
      return event
    })
    return { ...message, toolEvents }
  })
}

const parseSse = (buffer: string) => {
  const parts = buffer.split('\n\n')
  const rest = parts.pop() || ''
  const events = parts.map((part) => {
    const eventLine = part.split('\n').find((line) => line.startsWith('event: '))
    const dataLine = part.split('\n').find((line) => line.startsWith('data: '))
    return {
      event: eventLine?.slice(7) || 'message',
      data: dataLine ? JSON.parse(dataLine.slice(6)) : {}
    }
  })
  return { events, rest }
}

const stopGeneration = () => {
  if (currentAbortController) {
    currentAbortController.abort()
    currentAbortController = null
  }
  busy.value = false
  // Set streaming state to false on last assistant message
  if (messages.value.length > 0) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.streaming = false
    }
  }
}

const send = async (text: string) => {
  const trimmed = text.trim()
  if (!trimmed || busy.value) return

  errorText.value = ''
  connectionError.value = false

  let activeSid = currentSessionId.value
  if (!activeSid) {
    activeSid = await createSessionForMessage(trimmed)
  }

  const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: trimmed }
  const assistantId = crypto.randomUUID()
  messages.value.push(userMsg, { id: assistantId, role: 'assistant', content: '', streaming: true, toolEvents: [] })
  busy.value = true
  scrollToBottom()

  currentAbortController = new AbortController()

  try {
    const response = await fetch(`${config.public.apiBase}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        messages: messages.value
          .filter((message) => message.role === 'user' || (message.role === 'assistant' && message.content.trim()))
          .map((message) => ({ role: message.role, content: message.content })),
        max_rounds: 8,
        session_id: activeSid
      })
    })

    if (!response.ok || !response.body) throw new Error(`Chat request failed: ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSse(buffer)
      buffer = parsed.rest

      for (const item of parsed.events) {
        if (item.event === 'delta') {
          const current = messages.value.find((message) => message.id === assistantId)
          updateAssistant(assistantId, { content: `${current?.content || ''}${item.data.content || ''}` })
        } else if (item.event === 'replace_last') {
          updateAssistant(assistantId, { content: item.data.content || '' })
        } else if (item.event === 'tool_start') {
          addToolEvent(assistantId, {
            id: crypto.randomUUID(),
            name: item.data.name,
            input: item.data.input,
            status: 'running'
          })
        } else if (item.event === 'tool_result') {
          finishToolEvent(assistantId, item.data.name, item.data.output || '', item.data.ok !== false)
        } else if (item.event === 'error') {
          errorText.value = item.data.message || 'Agent failed'
          updateAssistant(assistantId, { content: errorText.value })
        } else if (item.event === 'done') {
          updateAssistant(assistantId, {
            streaming: false,
            metadata: {
              input_tokens: item.data.input_tokens,
              output_tokens: item.data.output_tokens,
              response_time_ms: item.data.response_time_ms
            }
          })
          busy.value = false
          // Session is now created on backend — update route or drawer state so refresh/bookmark works
          if (props.isInDrawer) {
            drawerSessionId.value = activeSid
          } else if (typeof route.query.session !== 'string') {
            router.replace({ path: '/chat', query: { session: activeSid } })
          }
          await loadSessions()
        }
        scrollToBottom()
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Stream aborted')
      return
    }
    connectionError.value = true
    errorText.value = 'Failed to connect to AI server. Please make sure the backend services are running.'
    updateAssistant(assistantId, { content: errorText.value, streaming: false })
    busy.value = false
  }
}

const regenerateResponse = async (assistantMsgId: string) => {
  if (busy.value) return
  errorText.value = ''
  connectionError.value = false

  let activeSid = currentSessionId.value
  if (!activeSid) return

  const idx = messages.value.findIndex(m => m.id === assistantMsgId)
  if (idx === -1) return

  // Truncate messages local state to keep everything before this assistant message
  messages.value = messages.value.slice(0, idx)

  const assistantId = crypto.randomUUID()
  messages.value.push({ id: assistantId, role: 'assistant', content: '', streaming: true, toolEvents: [] })
  busy.value = true
  scrollToBottom()

  currentAbortController = new AbortController()

  try {
    const response = await fetch(`${config.public.apiBase}/api/chat/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        session_id: activeSid,
        model: currentSessionModel.value || undefined
      })
    })

    if (!response.ok || !response.body) throw new Error(`Regenerate request failed: ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSse(buffer)
      buffer = parsed.rest

      for (const item of parsed.events) {
        if (item.event === 'delta') {
          const current = messages.value.find((message) => message.id === assistantId)
          updateAssistant(assistantId, { content: `${current?.content || ''}${item.data.content || ''}` })
        } else if (item.event === 'replace_last') {
          updateAssistant(assistantId, { content: item.data.content || '' })
        } else if (item.event === 'tool_start') {
          addToolEvent(assistantId, {
            id: crypto.randomUUID(),
            name: item.data.name,
            input: item.data.input,
            status: 'running'
          })
        } else if (item.event === 'tool_result') {
          finishToolEvent(assistantId, item.data.name, item.data.output || '', item.data.ok !== false)
        } else if (item.event === 'error') {
          errorText.value = item.data.message || 'Agent failed'
          updateAssistant(assistantId, { content: errorText.value })
        } else if (item.event === 'done') {
          updateAssistant(assistantId, {
            streaming: false,
            metadata: {
              input_tokens: item.data.input_tokens,
              output_tokens: item.data.output_tokens,
              response_time_ms: item.data.response_time_ms
            }
          })
          busy.value = false
          loadSessions()
        }
        scrollToBottom()
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Regenerate stream aborted')
      return
    }
    connectionError.value = true
    errorText.value = 'Failed to connect to AI server. Please make sure the backend services are running.'
    updateAssistant(assistantId, { content: errorText.value, streaming: false })
    busy.value = false
  }
}

onMounted(() => {
  loadSessions()
  const q = typeof route.query.q === 'string' ? route.query.q : ''
  if (q && !initialQuerySent.value) {
    initialQuerySent.value = true
    send(q)
  }
})

const empty = computed(() => messages.value.length === 0)
const filteredSessions = computed(() => activeTab.value === 'active' ? sessionsList.value : archivedSessionsList.value)
</script>

<template>
  <div class="flex-1 min-h-0 flex overflow-hidden">
    <!-- Left Panel: Collapsible Session Sidebar -->
    <div
      v-if="!sidebarCollapsed && !isInDrawer"
      class="w-72 border-r border-stone-200 dark:border-stone-800 bg-[#F5F5F4] dark:bg-stone-900/60 flex flex-col shrink-0 transition-all duration-300 relative"
    >
      <!-- Action and Title area -->
      <div class="p-4 flex flex-col gap-3 shrink-0">
        <button
          class="w-full flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm rounded-xl shadow-sm transition-colors duration-200"
          @click="startNewChat"
        >
          <Plus :size="16" />
          New Conversation
        </button>

        <!-- Search box -->
        <div class="relative flex items-center w-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 rounded-xl px-3 py-1.5 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-shadow">
          <Search :size="15" class="text-stone-400 shrink-0 mr-2" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search conversations..."
            class="w-full bg-transparent border-0 outline-none text-xs text-stone-700 dark:text-stone-300 placeholder-stone-400"
          />
        </div>

        <!-- Pill tabs selector -->
        <div class="flex bg-stone-200/60 dark:bg-stone-800/80 p-0.5 rounded-lg text-xs font-semibold text-stone-500 shrink-0">
          <button
            class="flex-1 py-1 rounded-md transition-all"
            :class="activeTab === 'active' ? 'bg-white dark:bg-stone-700 text-stone-900 dark:text-stone-100 shadow-sm' : 'hover:text-stone-800 dark:hover:text-stone-300'"
            @click="activeTab = 'active'"
          >
            Active
          </button>
          <button
            class="flex-1 py-1 rounded-md transition-all"
            :class="activeTab === 'archived' ? 'bg-white dark:bg-stone-700 text-stone-900 dark:text-stone-100 shadow-sm' : 'hover:text-stone-800 dark:hover:text-stone-300'"
            @click="activeTab = 'archived'"
          >
            Archived
          </button>
        </div>
      </div>

      <!-- Conversations list -->
      <div class="flex-1 overflow-y-auto px-2 pb-4 space-y-1 hide-scrollbar">
        <div
          v-if="filteredSessions.length === 0"
          class="text-center py-8 text-xs text-stone-400"
        >
          No conversations found
        </div>

        <div
          v-for="s in filteredSessions"
          :key="s.id"
          class="group flex items-center justify-between gap-2 p-3 rounded-xl cursor-pointer transition-all duration-200"
          :class="[
            currentSessionId === s.id
              ? 'bg-white dark:bg-stone-800 shadow-sm border border-stone-200/60 dark:border-stone-700 text-stone-900 dark:text-stone-100'
              : 'text-stone-600 dark:text-stone-400 hover:bg-stone-200/50 dark:hover:bg-stone-800/30'
          ]"
          @click="selectSession(s.id)"
        >
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <MessageSquare :size="16" class="text-stone-400 shrink-0" />

            <!-- Inline rename field -->
            <div v-if="editingSessionId === s.id" class="flex-1 min-w-0" @click.stop>
              <input
                ref="renameInput"
                v-model="editingName"
                class="w-full bg-white dark:bg-stone-800 border border-blue-500 text-xs px-2 py-0.5 rounded outline-none text-stone-900 dark:text-stone-100"
                @keydown.enter.stop="saveRename(s.id)"
                @keydown.esc.stop="editingSessionId = null"
                @blur="saveRename(s.id)"
              />
            </div>
            <div v-else class="flex-1 min-w-0 flex flex-col" @dblclick="startRename(s.id, s.name)">
              <span class="text-[13px] font-medium truncate leading-tight">{{ s.name }}</span>
              <span v-if="s.model" class="text-[10px] text-stone-400 truncate mt-0.5">{{ s.model }}</span>
            </div>
          </div>

          <!-- Interaction actions on right -->
          <div class="flex items-center gap-0.5 shrink-0" @click.stop>
            <span v-if="!s.is_important" class="text-[10px] text-stone-400/80 dark:text-stone-500/80 mr-1 group-hover:hidden">
              {{ formatRelativeTime(s.updated_at || s.created_at) }}
            </span>

            <!-- Star (Important) toggle -->
            <button
              class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-700 transition-colors"
              :class="s.is_important ? 'text-amber-500 opacity-100' : 'text-stone-400 opacity-0 group-hover:opacity-100'"
              title="Mark as important"
              @click="toggleImportant(s)"
            >
              <Star :size="13" :fill="s.is_important ? 'currentColor' : 'none'" />
            </button>

            <!-- Archive/Unarchive -->
            <button
              v-if="activeTab === 'active'"
              class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-700 text-stone-400 hover:text-stone-700 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Archive conversation"
              @click="archiveSession(s.id)"
            >
              <Archive :size="13" />
            </button>
            <button
              v-else
              class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-700 text-stone-400 hover:text-stone-700 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Restore conversation"
              @click="unarchiveSession(s.id)"
            >
              <ArchiveRestore :size="13" />
            </button>

            <!-- Delete -->
            <button
              class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-700 text-stone-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete conversation"
              @click="deleteSession(s.id)"
            >
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel: Main Chat Area -->
    <div class="flex-1 flex flex-col min-w-0 bg-white dark:bg-stone-950 relative">
      <!-- Chat Pane Header -->
      <div class="h-14 border-b border-stone-200 dark:border-stone-800 px-6 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-3">
          <button
            v-if="!isInDrawer"
            class="p-1.5 rounded-lg text-stone-500 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
            @click="sidebarCollapsed = !sidebarCollapsed"
          >
            <ChevronRight v-if="sidebarCollapsed" :size="18" />
            <ChevronLeft v-else :size="18" />
          </button>

          <div class="flex flex-col">
            <h2 class="text-sm font-semibold text-stone-800 dark:text-stone-100 leading-tight">
              {{ currentSessionName }}
            </h2>
            <span v-if="currentSessionModel" class="text-[10px] text-stone-400 font-mono mt-0.5">
              {{ currentSessionModel }}
            </span>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div v-if="busy" class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 text-xs font-medium">
            <Sparkles :size="12" class="animate-spin" />
            Thinking...
          </div>

          <button
            v-if="isInDrawer"
            class="p-1.5 rounded-lg text-stone-500 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            title="Close Chat"
            @click="isChatDrawerOpen = false"
          >
            <X :size="18" />
          </button>
        </div>
      </div>

      <!-- Messages Stream Scroll Workspace -->
      <div
        ref="scrollRef"
        class="flex-1 overflow-y-auto px-6 hide-scrollbar relative"
        @scroll="handleScroll"
      >
        <div class="max-w-3xl mx-auto w-full py-8">

          <!-- Connection Error Alert Banner -->
          <div v-if="connectionError" class="mb-6 p-4 rounded-xl border border-red-200 bg-red-50 text-red-800 dark:bg-red-950/30 dark:border-red-900/60 dark:text-red-400 text-sm flex gap-3 items-start shadow-sm">
            <AlertTriangle class="shrink-0 text-red-500 mt-0.5" :size="18" />
            <div>
              <h4 class="font-bold mb-1">Server Connection Offline</h4>
              <p>{{ errorText }}</p>
            </div>
          </div>

          <!-- Empty state -->
          <div
            v-if="empty"
            class="flex flex-col items-center justify-center text-center py-24"
          >
            <div class="text-blue-600 dark:text-blue-500 mb-5 animate-pulse">
              <Waves
                :size="48"
                :stroke-width="1.5"
              />
            </div>
            <h1 class="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
              Start a conversation
            </h1>
            <p class="text-stone-500 dark:text-stone-400 max-w-md text-sm">
              Ask a question and NAGARE will answer using your connected knowledge base, executing tools dynamically in the background.
            </p>
          </div>

          <!-- Chat bubble list -->
          <div
            v-else
            class="space-y-8"
          >
            <TransitionGroup
              name="list"
              tag="div"
              class="space-y-8"
            >
              <ChatMessageBubble
                v-for="(m, index) in messages"
                :key="m.id"
                :message="m"
                :is-last="index === messages.length - 1"
                :busy="busy"
                @regenerate="regenerateResponse"
              >
                <template #avatar>
                  <User
                    v-if="m.role === 'user'"
                    :size="16"
                    :stroke-width="1.5"
                  />
                  <Waves
                    v-else
                    :size="16"
                    :stroke-width="2"
                  />
                </template>
              </ChatMessageBubble>
            </TransitionGroup>
          </div>
        </div>

        <!-- Floating Scroll to Bottom pill -->
        <button
          v-if="showScrollButton"
          class="absolute bottom-4 right-8 flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg text-xs font-semibold select-none z-10 transition-transform active:scale-95"
          @click="forceScrollToBottom"
        >
          <ArrowDown :size="14" />
          Recent message
        </button>
      </div>

      <!-- Composer at bottom -->
      <div class="px-6 pb-6 pt-2 shrink-0 bg-gradient-to-t from-white dark:from-stone-950 via-white dark:via-stone-950 to-transparent">
        <div class="max-w-3xl mx-auto w-full">
          <ChatComposer
            :busy="busy"
            @send="send"
            @stop="stopGeneration"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-enter-active {
  transition: all 0.3s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
</style>
