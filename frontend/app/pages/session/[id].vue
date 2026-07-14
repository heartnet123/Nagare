<script setup lang="ts">
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import {
  Waves,
  ChevronLeft,
  MessageSquare,
  Sparkles,
  AlertTriangle,
  ArrowDown,
  User,
} from '@lucide/vue'
import { useChatSession } from '~/composables/useChatSession'

definePageMeta({
  layout: 'default',
})

// ── Markdown setup ───────────────────────────────────────────────────────────
marked.use({
  renderer: {
    code(token: any) {
      const codeText = token.text || ''
      const lang = token.lang || 'plaintext'
      let highlighted = codeText
      try {
        highlighted = hljs.highlight(codeText, { language: lang }).value
      } catch {
        try {
          highlighted = hljs.highlightAuto(codeText).value
        } catch {
          highlighted = codeText
        }
      }
      return `<pre class="overflow-auto bg-stone-900 text-stone-100 p-4 rounded-xl font-mono text-sm my-3 border border-stone-800"><code class="hljs language-${lang}">${highlighted}</code></pre>`
    },
  },
})

function renderMarkdown(text: string): string {
  if (!text) return ''
  try {
    const raw = marked.parse(text) as string
    return DOMPurify.sanitize(raw)
  } catch {
    return text
  }
}

// ── Route & config ───────────────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()

const {
  messages,
  busy,
  errorText,
  connectionError,
  send,
  stopGeneration,
  loadSessionHistory,
} = useChatSession(config.public.apiBase)

// ── UI State ─────────────────────────────────────────────────────────────────
const scrollRef = ref<HTMLDivElement | null>(null)
const showScrollButton = ref(false)
const initialLoading = ref(true)
const sessionName = ref('Chat')
const sessionModel = ref('')

const { syncSelectionToModel } = useActiveSelection()

watch(sessionModel, (newModel) => {
  if (newModel) {
    syncSelectionToModel(newModel)
  }
}, { immediate: true })

// ── Computed ─────────────────────────────────────────────────────────────────
const hasMessages = computed(() => messages.value.length > 0)

// ── Scroll ───────────────────────────────────────────────────────────────────
function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTo({
        top: scrollRef.value.scrollHeight,
        behavior: 'smooth',
      })
    }
  })
}

function handleScroll() {
  if (!scrollRef.value) return
  const { scrollTop, scrollHeight, clientHeight } = scrollRef.value
  showScrollButton.value = scrollHeight - scrollTop - clientHeight > 400
}

function forceScrollToBottom() {
  if (scrollRef.value) {
    scrollRef.value.scrollTo({
      top: scrollRef.value.scrollHeight,
      behavior: 'smooth',
    })
  }
}

// ── Watcher for auto-scroll ──────────────────────────────────────────────────
watch(
  () => messages.value.length,
  () => {
    if (scrollRef.value && !showScrollButton.value) {
      scrollToBottom()
    }
  },
)

// ── Load session + initial query ─────────────────────────────────────────────
onMounted(async () => {
  const sid = route.params.id as string
  if (!sid) {
    router.replace('/')
    return
  }

  // Load session metadata
  try {
    const session = await $fetch(`/api/session/${sid}`, {
      baseURL: config.public.apiBase,
    }) as any
    sessionName.value = session.name || 'Chat'
    sessionModel.value = session.model || ''
  } catch {
    sessionName.value = 'Chat'
  }

  // Load existing message history
  try {
    await loadSessionHistory(sid)
  } catch {
    // Session may be fresh — that's fine
  }

  initialLoading.value = false

  // Auto-send initial query if redirected with ?q=
  const q = route.query.q as string | undefined
  if (q && messages.value.length === 0) {
    await nextTick()
    await send(q)
    // Clean query param from URL after sending
    router.replace({ query: {} })
  }

  scrollToBottom()
})
</script>

<template>
  <div class="flex-1 flex flex-col min-h-0 bg-white dark:bg-stone-950">
    <!-- ── Header ────────────────────────────────────────────────────── -->
    <header
      class="h-14 border-b border-stone-200 dark:border-stone-800 px-4 sm:px-6 flex items-center justify-between shrink-0 bg-white/80 dark:bg-stone-950/80 backdrop-blur-sm sticky top-0 z-10"
    >
      <div class="flex items-center gap-3 min-w-0">
        <button
          class="p-1.5 rounded-lg text-stone-500 dark:text-stone-400 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          title="Back to home"
          @click="router.push('/')"
        >
          <ChevronLeft :size="20" />
        </button>
        <div class="flex flex-col min-w-0">
          <h1 class="text-sm font-semibold text-stone-800 dark:text-stone-100 truncate leading-tight">
            {{ sessionName }}
          </h1>
          <span
            v-if="sessionModel"
            class="text-[10px] text-stone-400 font-mono truncate"
          >
            {{ sessionModel }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <div
          v-if="busy"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 text-xs font-medium"
        >
          <Sparkles :size="12" class="animate-spin" />
          Thinking...
        </div>
        <button
          class="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          title="New conversation"
          @click="router.push('/')"
        >
          <MessageSquare :size="16" />
        </button>
      </div>
    </header>

    <!-- ── Messages Area ─────────────────────────────────────────────── -->
    <div
      ref="scrollRef"
      class="flex-1 overflow-y-auto hide-scrollbar relative"
      @scroll="handleScroll"
    >
      <div class="max-w-3xl mx-auto w-full px-4 sm:px-6 py-6">

        <!-- Loading skeleton -->
        <div
          v-if="initialLoading"
          class="flex flex-col items-center justify-center py-24"
        >
          <div class="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4" />
          <p class="text-sm text-stone-400">Loading conversation...</p>
        </div>

        <!-- Connection Error Banner -->
        <div
          v-if="connectionError"
          class="mb-6 p-4 rounded-xl border border-red-200 bg-red-50 text-red-800 dark:bg-red-950/30 dark:border-red-900/60 dark:text-red-400 text-sm flex gap-3 items-start shadow-sm"
        >
          <AlertTriangle class="shrink-0 text-red-500 mt-0.5" :size="18" />
          <div>
            <h4 class="font-bold mb-1">Connection Offline</h4>
            <p>{{ errorText }}</p>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="!initialLoading && !hasMessages && !connectionError"
          class="flex flex-col items-center justify-center text-center py-24"
        >
          <div class="text-blue-600 dark:text-blue-500 mb-5">
            <Waves :size="48" :stroke-width="1.5" class="animate-pulse" />
          </div>
          <h1 class="text-2xl font-semibold text-stone-900 dark:text-stone-100 mb-2">
            Start a conversation
          </h1>
          <p class="text-stone-500 dark:text-stone-400 max-w-md text-sm">
            Ask a question and NAGARE will answer using your connected knowledge base and tools.
          </p>
        </div>

        <!-- Message List (ChatGPT-style alignment) -->
        <div
          v-if="!initialLoading && hasMessages"
          class="space-y-6"
        >
          <div
            v-for="m in messages"
            :key="m.id"
            class="flex gap-3 items-start animate-fade-in"
            :class="m.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
          >
            <!-- Avatar -->
            <div class="shrink-0 flex items-start pt-1">
              <div
                v-if="m.role === 'user'"
                class="w-8 h-8 rounded-full bg-gradient-to-br from-stone-400 to-stone-500 flex items-center justify-center shadow-sm"
              >
                <User :size="16" class="text-white" />
              </div>
              <div
                v-else
                class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm"
              >
                <Waves :size="16" :stroke-width="2" class="text-white" />
              </div>
            </div>

            <!-- Bubble Column -->
            <div
              class="min-w-0 max-w-[85%] sm:max-w-[75%] flex flex-col"
              :class="m.role === 'user' ? 'items-end' : 'items-start'"
            >
              <!-- Label -->
              <div
                class="flex items-center gap-2 mb-1 px-1"
                :class="m.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
              >
                <span
                  class="text-[11px] font-semibold tracking-wide"
                  :class="m.role === 'user' ? 'text-stone-400 dark:text-stone-500' : 'text-blue-600 dark:text-blue-400'"
                >
                  {{ m.role === 'user' ? 'You' : 'NAGARE' }}
                </span>
              </div>

              <!-- Bubble -->
              <div
                class="rounded-2xl px-4 py-3 text-[15px] leading-relaxed"
                :class="
                  m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md shadow-sm'
                    : 'bg-stone-100 dark:bg-stone-800/80 text-stone-800 dark:text-stone-200 rounded-bl-md border border-stone-200/50 dark:border-stone-700/50 shadow-sm'
                "
              >
                <!-- User: plain text -->
                <template v-if="m.role === 'user'">
                  <p class="whitespace-pre-wrap break-words">{{ m.content }}</p>
                </template>

                <!-- Assistant: rich markdown -->
                <template v-else>
                  <div
                    v-if="m.content"
                    class="markdown-body"
                    v-html="renderMarkdown(m.content)"
                  />
                  <span
                    v-if="m.streaming"
                    class="inline-block w-1.5 h-4 ml-0.5 -mb-0.5 bg-blue-500 rounded-sm animate-pulse"
                  />

                  <!-- Tool Events -->
                  <div
                    v-if="m.toolEvents && m.toolEvents.length > 0"
                    class="mt-3 pt-3 border-t border-stone-200/60 dark:border-stone-700/60 space-y-1.5"
                  >
                    <div
                      v-for="tool in m.toolEvents"
                      :key="tool.id"
                      class="flex items-center gap-2 text-xs"
                      :class="
                        tool.status === 'running'
                          ? 'text-blue-500'
                          : tool.status === 'error'
                            ? 'text-red-500'
                            : 'text-stone-500 dark:text-stone-400'
                      "
                    >
                      <span
                        class="w-1.5 h-1.5 rounded-full shrink-0"
                        :class="
                          tool.status === 'running'
                            ? 'bg-blue-500 animate-pulse'
                            : tool.status === 'error'
                              ? 'bg-red-500'
                              : 'bg-emerald-500'
                        "
                      />
                      <span class="font-medium">{{ tool.name }}</span>
                      <span
                        v-if="tool.status === 'running'"
                        class="text-stone-400"
                      >running...</span>
                    </div>
                  </div>

                  <!-- Token / timing footer -->
                  <div
                    v-if="!m.streaming && m.metadata"
                    class="mt-3 flex items-center gap-3 text-[10px] text-stone-400 font-mono"
                  >
                    <span v-if="m.metadata.output_tokens !== undefined">
                      {{ m.metadata.output_tokens }} tok
                    </span>
                    <span v-if="m.metadata.input_tokens !== undefined">
                      in: {{ m.metadata.input_tokens }}
                    </span>
                    <span v-if="m.metadata.response_time_ms !== undefined">
                      {{ (m.metadata.response_time_ms / 1000).toFixed(1) }}s
                    </span>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scroll-to-bottom pill -->
      <button
        v-if="showScrollButton"
        class="sticky bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg text-xs font-semibold select-none z-10 transition-transform active:scale-95"
        @click="forceScrollToBottom"
      >
        <ArrowDown :size="14" />
        New messages
      </button>
    </div>

    <!-- ── Composer ──────────────────────────────────────────────────── -->
    <div class="border-t border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 px-4 sm:px-6 py-4 shrink-0">
      <div class="max-w-3xl mx-auto w-full">
        <ChatComposer
          :busy="busy"
          @send="send"
          @stop="stopGeneration"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Fade-in animation */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.25s ease-out;
}

/* Markdown content styling */
.markdown-body :deep(p) {
  margin-bottom: 0.75rem;
}
.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-top: 0.5rem;
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
}
.markdown-body :deep(ul) { list-style-type: disc; }
.markdown-body :deep(ol) { list-style-type: decimal; }
.markdown-body :deep(li) { margin-bottom: 0.25rem; }
.markdown-body :deep(strong) { font-weight: 600; }
.markdown-body :deep(code:not(.hljs)) {
  font-family: monospace;
  font-size: 0.875rem;
  padding: 0.125rem 0.375rem;
  border-radius: 0.375rem;
  background-color: #f3f4f6;
}
:deep(.dark) .markdown-body code:not(.hljs) {
  background-color: #1c1917;
}
.markdown-body :deep(pre) {
  margin: 0.75rem 0;
  border-radius: 0.75rem;
  overflow-x: auto;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
.markdown-body :deep(h1) { font-size: 1.2rem; }
.markdown-body :deep(h2) { font-size: 1.1rem; }
.markdown-body :deep(h3) { font-size: 1rem; }
.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}
:deep(.dark) .markdown-body a { color: #60a5fa; }
.markdown-body :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: #6b7280;
  font-style: italic;
}
:deep(.dark) .markdown-body blockquote {
  border-left-color: #4b5563;
  color: #9ca3af;
}
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 0.875rem;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
:deep(.dark) .markdown-body th,
:deep(.dark) .markdown-body td { border-color: #374151; }
.markdown-body :deep(th) {
  background-color: #f9fafb;
  font-weight: 600;
}
:deep(.dark) .markdown-body th { background-color: #1f2937; }
</style>
