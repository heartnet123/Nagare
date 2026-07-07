<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Waves, ArrowUp, FileText, User, Wrench } from '@lucide/vue'

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
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  toolEvents?: ToolEvent[]
}

const route = useRoute()
const config = useRuntimeConfig()
const messages = ref<Message[]>([])
const input = ref('')
const busy = ref(false)
const scrollRef = ref<HTMLDivElement | null>(null)
const seededRef = ref(false)
const errorText = ref('')

const scrollToBottom = () => {
  nextTick(() => {
    scrollRef.value?.scrollTo({
      top: scrollRef.value.scrollHeight,
      behavior: 'smooth'
    })
  })
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

const send = async (text: string) => {
  const trimmed = text.trim()
  if (!trimmed || busy.value) return

  errorText.value = ''
  const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: trimmed }
  const assistantId = crypto.randomUUID()
  messages.value.push(userMsg, { id: assistantId, role: 'assistant', content: '', streaming: true, toolEvents: [] })
  input.value = ''
  busy.value = true
  scrollToBottom()

  try {
    const response = await fetch(`${config.public.apiBase}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: messages.value
          .filter((message) => message.role === 'user' || (message.role === 'assistant' && message.content.trim()))
          .map((message) => ({ role: message.role, content: message.content })),
        max_rounds: 8
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
          updateAssistant(assistantId, { streaming: false })
          busy.value = false
        }
        scrollToBottom()
      }
    }
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Chat request failed'
    updateAssistant(assistantId, { content: errorText.value, streaming: false })
    busy.value = false
  }
}

onMounted(() => {
  if (seededRef.value) return
  seededRef.value = true
  const q = typeof route.query.q === 'string' ? route.query.q : ''
  if (q) send(q)
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    if (e.isComposing) return
    e.preventDefault()
    send(input.value)
  }
}

const empty = computed(() => messages.value.length === 0)
</script>

<template>
  <div class="flex-1 min-h-0 flex flex-col">
    <div
      ref="scrollRef"
      class="flex-1 overflow-y-auto px-6 hide-scrollbar"
    >
      <div class="max-w-3xl mx-auto w-full py-8">
        <div
          v-if="empty"
          class="flex flex-col items-center justify-center text-center py-24"
        >
          <div class="text-blue-600 mb-5">
            <Waves
              :size="48"
              :stroke-width="1.5"
            />
          </div>
          <h1 class="text-2xl font-semibold text-stone-900 mb-2">
            Start a conversation
          </h1>
          <p class="text-stone-500 max-w-md">
            Ask a question and NAGARE will answer using your connected knowledge base, citing
            the sources it used.
          </p>
        </div>

        <div
          v-else
          class="space-y-8"
        >
          <TransitionGroup
            name="list"
            tag="div"
            class="space-y-8"
          >
            <div
              v-for="m in messages"
              :key="m.id"
              class="flex gap-4"
            >
              <div
                class="shrink-0 flex items-center justify-center w-8 h-8 rounded-full"
                :class="m.role === 'user' ? 'bg-stone-200 text-stone-600' : 'bg-blue-600 text-white'"
              >
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
              </div>
              <div class="min-w-0 flex-1 pt-0.5">
                <div class="text-xs font-semibold text-stone-500 mb-1.5">
                  {{ m.role === 'user' ? 'You' : 'NAGARE' }}
                </div>
                <div class="text-[15px] leading-relaxed text-stone-800 whitespace-pre-wrap">
                  {{ m.content }}
                  <span
                    v-if="m.streaming"
                    class="inline-block w-1.5 h-4 ml-0.5 -mb-0.5 bg-blue-500 rounded-sm animate-pulse"
                  />
                </div>
                <div
                  v-if="m.toolEvents && m.toolEvents.length > 0"
                  class="mt-4 space-y-2"
                >
                  <div class="text-[11px] font-semibold uppercase tracking-wider text-stone-400 mb-2">
                    Tool activity
                  </div>
                  <div
                    v-for="tool in m.toolEvents"
                    :key="tool.id"
                    class="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-600"
                  >
                    <div class="flex items-center justify-between gap-2 mb-1">
                      <span class="flex items-center gap-1.5 font-semibold text-stone-700">
                        <Wrench :size="13" />
                        {{ tool.name }}
                      </span>
                      <span
                        class="text-[10px] font-semibold uppercase"
                        :class="tool.status === 'error' ? 'text-red-600' : tool.status === 'done' ? 'text-emerald-600' : 'text-blue-600'"
                      >
                        {{ tool.status }}
                      </span>
                    </div>
                    <pre v-if="tool.output" class="max-h-32 overflow-auto whitespace-pre-wrap rounded-lg bg-stone-50 p-2">{{ tool.output }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </div>
    </div>

    <!-- Composer -->
    <div class="px-6 pb-6 pt-2 shrink-0">
      <div class="max-w-3xl mx-auto w-full">
        <div class="relative w-full bg-white rounded-2xl shadow-sm border border-stone-200/80 overflow-hidden flex flex-col transition-shadow duration-300 focus-within:ring-4 focus-within:ring-blue-50 focus-within:border-blue-300">
          <textarea
            v-model="input"
            class="w-full h-20 p-4 resize-none bg-transparent outline-none text-stone-800 placeholder-stone-400"
            placeholder="Ask a follow-up..."
            aria-label="Message input"
            @keydown="handleKeyDown"
          />
          <div class="flex items-center justify-end px-3 py-2.5 gap-2 bg-white">
            <button
              class="p-2 text-stone-400 hover:text-stone-600 transition-colors"
              aria-label="Attach file"
            >
              <Paperclip
                :size="18"
                :stroke-width="1.5"
              />
            </button>
            <button
              :disabled="busy || !input.trim()"
              class="flex items-center justify-center w-9 h-9 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white shadow-sm transition-colors"
              aria-label="Send message"
              @click="send(input)"
            >
              <ArrowUp
                :size="18"
                :stroke-width="2"
              />
            </button>
          </div>
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
