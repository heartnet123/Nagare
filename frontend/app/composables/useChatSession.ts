/**
 * Composable for managing a single chat session — send, SSE stream, stop, regenerate.
 *
 * Extracted from ChatView.vue for reuse in the dedicated /session/[id] page.
 */
import { ref, type Ref } from 'vue'

interface ToolEvent {
  id: string
  name: string
  input?: unknown
  output?: string
  error?: string
  status: 'running' | 'done' | 'error'
}

export interface ChatMessage {
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

export function useChatSession(apiBase: string) {
  const { activeModelName } = useActiveSelection()
  // ── State ──────────────────────────────────────────────────────────────────
  const messages = ref<ChatMessage[]>([]) as Ref<ChatMessage[]>
  const busy = ref(false)
  const errorText = ref('')
  const connectionError = ref(false)
  const currentSessionId = ref<string | null>(null)
  let currentAbortController: AbortController | null = null

  // ── Helpers ────────────────────────────────────────────────────────────────

  function updateAssistant(id: string, patch: Partial<ChatMessage>) {
    messages.value = messages.value.map(msg =>
      msg.id === id ? { ...msg, ...patch } : msg
    )
  }

  function addToolEvent(assistantId: string, event: ToolEvent) {
    messages.value = messages.value.map((msg) => {
      if (msg.id !== assistantId) return msg
      return { ...msg, toolEvents: [...(msg.toolEvents || []), event] }
    })
  }

  function finishToolEvent(assistantId: string, name: string, output: string, ok = true) {
    messages.value = messages.value.map((msg) => {
      if (msg.id !== assistantId) return msg
      const toolEvents = (msg.toolEvents || []).map((ev) => {
        if (ev.name === name && ev.status === 'running') {
          return { ...ev, output, status: (ok ? 'done' : 'error') as 'done' | 'error' }
        }
        return ev
      })
      return { ...msg, toolEvents }
    })
  }

  function parseSse(buffer: string) {
    const parts = buffer.split('\n\n')
    const rest = parts.pop() || ''
    const events = parts.map((part) => {
      const eventLine = part.split('\n').find(line => line.startsWith('event: '))
      const dataLine = part.split('\n').find(line => line.startsWith('data: '))
      return {
        event: eventLine?.slice(7) || 'message',
        data: dataLine ? JSON.parse(dataLine.slice(6)) : {}
      }
    })
    return { events, rest }
  }

  function formatHistoryMessages(apiMessages: any[]): ChatMessage[] {
    const formatted: ChatMessage[] = []
    let lastAssistant: ChatMessage | null = null

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
        const newMsg: ChatMessage = {
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
        lastAssistant = msg.role === 'assistant' ? newMsg : null
      }
    }
    return formatted
  }

  // ── Core actions ───────────────────────────────────────────────────────────

  function stopGeneration() {
    if (currentAbortController) {
      currentAbortController.abort()
      currentAbortController = null
    }
    busy.value = false
    if (messages.value.length > 0) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.streaming = false
      }
    }
  }

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || busy.value) return

    errorText.value = ''
    connectionError.value = false

    let activeSid = currentSessionId.value
    if (!activeSid) {
      // Generate a UUID and create session on the backend
      activeSid = crypto.randomUUID()
      try {
        const session = await $fetch('/api/session', {
          method: 'POST',
          baseURL: apiBase,
          body: {
            name: trimmed.length > 48 ? `${trimmed.slice(0, 45)}...` : trimmed,
            model: activeModelName.value || undefined
          }
        })
        activeSid = (session as any).id
        currentSessionId.value = activeSid
      } catch {
        // Fallback: use UUID and let /api/chat/stream auto-create it
        currentSessionId.value = activeSid
      }
    }

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed }
    const assistantId = crypto.randomUUID()
    messages.value.push(userMsg, {
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      toolEvents: []
    })
    busy.value = true

    currentAbortController = new AbortController()

    try {
      const response = await fetch(`${apiBase}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: currentAbortController.signal,
        body: JSON.stringify({
          messages: messages.value
            .filter(
              msg => msg.role === 'user' || (msg.role === 'assistant' && msg.content.trim())
            )
            .map(msg => ({ role: msg.role, content: msg.content })),
          max_rounds: 8,
          session_id: activeSid,
          model: activeModelName.value || undefined
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
            const current = messages.value.find(msg => msg.id === assistantId)
            updateAssistant(assistantId, {
              content: `${current?.content || ''}${item.data.content || ''}`
            })
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
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return
      connectionError.value = true
      errorText.value = 'Failed to connect to AI server. Please make sure the backend services are running.'
      updateAssistant(assistantId, { content: errorText.value, streaming: false })
      busy.value = false
    }
  }

  async function regenerateResponse(assistantMsgId: string) {
    if (busy.value) return
    errorText.value = ''
    connectionError.value = false

    const activeSid = currentSessionId.value
    if (!activeSid) return

    const idx = messages.value.findIndex(m => m.id === assistantMsgId)
    if (idx === -1) return

    messages.value = messages.value.slice(0, idx)

    const assistantId = crypto.randomUUID()
    messages.value.push({
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      toolEvents: []
    })
    busy.value = true

    currentAbortController = new AbortController()

    try {
      const response = await fetch(`${apiBase}/api/chat/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: currentAbortController.signal,
        body: JSON.stringify({
          session_id: activeSid,
          model: activeModelName.value || undefined
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
            const current = messages.value.find(msg => msg.id === assistantId)
            updateAssistant(assistantId, {
              content: `${current?.content || ''}${item.data.content || ''}`
            })
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
          }
        }
      }
    } catch (error: any) {
      if (error.name === 'AbortError') return
      connectionError.value = true
      errorText.value = 'Failed to connect to AI server. Please make sure the backend services are running.'
      updateAssistant(assistantId, { content: errorText.value, streaming: false })
      busy.value = false
    }
  }

  async function loadSessionHistory(sessionId: string) {
    currentSessionId.value = sessionId
    try {
      const history = await $fetch(`/api/history/${sessionId}`, { baseURL: apiBase })
      messages.value = formatHistoryMessages(history as any[])
    } catch {
      errorText.value = 'Failed to load conversation history.'
    }
  }

  function reset() {
    messages.value = []
    busy.value = false
    errorText.value = ''
    connectionError.value = false
    currentSessionId.value = null
    currentAbortController = null
  }

  return {
    // State
    messages,
    busy,
    errorText,
    connectionError,
    currentSessionId,
    // Actions
    send,
    stopGeneration,
    regenerateResponse,
    loadSessionHistory,
    reset
  }
}
