<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import {
  Copy,
  Check,
  RotateCw,
  Clock,
  Coins,
  FileText
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

const props = defineProps<{
  message: Message
  isLast: boolean
  busy: boolean
}>()

const emit = defineEmits<{
  (e: 'regenerate', id: string): void
}>()

const copied = ref(false)

// Configure marked with custom code syntax highlighting
marked.use({
  renderer: {
    code(token: any) {
      const codeText = token.text || ''
      const lang = token.lang || 'plaintext'
      let highlighted = codeText
      try {
        highlighted = hljs.highlight(codeText, { language: lang }).value
      } catch {
        highlighted = hljs.highlightAuto(codeText).value
      }
      return `<pre class="overflow-auto bg-stone-900 text-stone-100 p-4 rounded-xl font-mono text-sm my-3 border border-stone-800"><code class="hljs language-${lang}">${highlighted}</code></pre>`
    }
  }
})

const parsedSources = computed(() => {
  const regex = /\[Source:\s*([^,\]]+)(?:,\s*page\s*(\d+))?\]/gi
  const list: Array<{ file: string, page: number | null }> = []
  let match
  // Extract sources
  while ((match = regex.exec(props.message.content)) !== null) {
    const filename = match[1] || ''
    const pageStr = match[2] || ''
    list.push({
      file: filename.trim(),
      page: pageStr ? parseInt(pageStr) : null
    })
  }
  // deduplicate
  return list.filter((v, i, a) => a.findIndex(t => t.file === v.file && t.page === v.page) === i)
})

const renderedHtml = computed(() => {
  let text = props.message.content
  if (!text) return ''

  // Replace sources text with styled superscript citations
  const regex = /\[Source:\s*([^,\]]+)(?:,\s*page\s*(\d+))?\]/gi
  let match
  let index = 1
  const map = new Map<string, number>()

  text = text.replace(regex, (full, file, page) => {
    const key = `${file.trim()}-${page ? page.trim() : ''}`
    if (!map.has(key)) {
      map.set(key, index++)
    }
    const idx = map.get(key)
    return ` <span class="inline-flex items-center justify-center px-1.5 py-0.2 ml-0.5 text-[9px] font-bold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-200 cursor-pointer select-none vertical-align-super" title="${file}${page ? ', Page ' + page : ''}">[${idx}]</span>`
  })

  try {
    const rawHtml = marked.parse(text) as string
    return DOMPurify.sanitize(rawHtml)
  } catch (e) {
    return text
  }
})

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy text:', err)
  }
}
</script>

<template>
  <div class="group relative flex gap-4 transition-all py-1">
    <!-- Role Avatar -->
    <div
      class="shrink-0 flex items-center justify-center w-8 h-8 rounded-full"
      :class="props.message.role === 'user' ? 'bg-stone-200 dark:bg-stone-800 text-stone-600 dark:text-stone-300' : 'bg-blue-600 text-white'"
    >
      <slot name="avatar" />
    </div>

    <!-- Content Bubble Container -->
    <div class="min-w-0 flex-1 pt-0.5">
      <div class="flex items-center justify-between gap-2 mb-1.5">
        <span class="text-xs font-semibold text-stone-500 dark:text-stone-400">
          {{ props.message.role === 'user' ? 'You' : 'NAGARE' }}
        </span>

        <!-- Quick actions (hover triggered) -->
        <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 transition-colors"
            title="Copy message"
            @click="copyText"
          >
            <Check
              v-if="copied"
              :size="14"
              class="text-emerald-500"
            />
            <Copy
              v-else
              :size="14"
            />
          </button>
          <button
            v-if="props.message.role === 'assistant' && !props.busy && props.isLast"
            class="p-1 rounded hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-400 hover:text-stone-700 dark:hover:text-stone-200 transition-colors"
            title="Regenerate response"
            @click="emit('regenerate', props.message.id)"
          >
            <RotateCw :size="14" />
          </button>
        </div>
      </div>

      <!-- Main Message Text / Markdown -->
      <div class="text-[15px] leading-relaxed text-stone-800 dark:text-stone-200 markdown-content">
        <div v-html="renderedHtml" />
        <span
          v-if="props.message.streaming"
          class="inline-block w-1.5 h-4 ml-0.5 -mb-0.5 bg-blue-500 rounded-sm animate-pulse"
        />
      </div>

      <!-- Source Citations List -->
      <div
        v-if="parsedSources.length > 0"
        class="mt-4 flex flex-wrap gap-2 pt-2 border-t border-stone-100 dark:border-stone-800"
      >
        <div class="text-[10px] uppercase font-bold tracking-wider text-stone-400 mr-2 flex items-center h-6">
          Sources:
        </div>
        <div
          v-for="(source, idx) in parsedSources"
          :key="idx"
          class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-stone-50 dark:bg-stone-900 border border-stone-200/60 dark:border-stone-850 text-xs text-stone-600 dark:text-stone-300"
        >
          <FileText
            :size="12"
            class="text-stone-400"
          />
          <span class="font-medium truncate max-w-[150px]">{{ source.file }}</span>
          <span
            v-if="source.page"
            class="text-[10px] text-stone-400 font-semibold px-1 rounded bg-stone-200/50 dark:bg-stone-800"
          >p. {{ source.page }}</span>
          <span class="text-[10px] font-bold text-blue-600 dark:text-blue-400">[{{ idx + 1 }}]</span>
        </div>
      </div>

      <!-- Token Count and Response Time Statistics -->
      <div
        v-if="props.message.role === 'assistant' && props.message.metadata"
        class="mt-3 flex items-center gap-4 text-[10px] text-stone-400 font-mono tracking-wide"
      >
        <span
          v-if="props.message.metadata.response_time_ms !== undefined"
          class="flex items-center gap-1"
        >
          <Clock :size="11" />
          {{ (props.message.metadata.response_time_ms / 1000).toFixed(2) }}s
        </span>
        <span
          v-if="props.message.metadata.input_tokens !== undefined"
          class="flex items-center gap-1"
        >
          <Coins :size="11" />
          In: {{ props.message.metadata.input_tokens }}
        </span>
        <span
          v-if="props.message.metadata.output_tokens !== undefined"
          class="flex items-center gap-1"
        >
          Out: {{ props.message.metadata.output_tokens }}
        </span>
      </div>
    </div>
  </div>
</template>

<style>
.markdown-content p {
  margin-bottom: 0.75rem;
}
.markdown-content p:last-child {
  margin-bottom: 0;
}
.markdown-content ul, .markdown-content ol {
  margin-top: 0.5rem;
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
}
.markdown-content ul {
  list-style-type: disc;
}
.markdown-content ol {
  list-style-type: decimal;
}
.markdown-content li {
  margin-bottom: 0.25rem;
}
.markdown-content strong {
  font-weight: 600;
}
.markdown-content code:not(.hljs) {
  font-family: monospace;
  font-size: 0.875rem;
  padding: 0.125rem 0.25rem;
  border-radius: 0.375rem;
  background-color: var(--tw-prose-pre-bg, #f3f4f6);
}
.dark .markdown-content code:not(.hljs) {
  background-color: #1c1917;
}
.markdown-content h1, .markdown-content h2, .markdown-content h3 {
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: inherit;
}
.markdown-content h1 { font-size: 1.25rem; }
.markdown-content h2 { font-size: 1.125rem; }
.markdown-content h3 { font-size: 1rem; }
</style>
