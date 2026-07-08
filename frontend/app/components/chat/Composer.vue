<script setup lang="ts">
import { ref, computed } from 'vue'
import { Paperclip, ArrowUp, Square, Loader2 } from '@lucide/vue'

const props = defineProps<{
  busy: boolean
}>()

const emit = defineEmits<{
  (e: 'send', val: string): void
  (e: 'stop'): void
}>()

const text = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const api = useApi()

const submit = () => {
  const trimmed = text.value.trim()
  if (!trimmed || props.busy) return
  emit('send', trimmed)
  text.value = ''
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    if (e.isComposing) return
    e.preventDefault()
    submit()
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileChange = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const res = await api.knowledge.upload(file)
    alert(`Document "${res.title}" uploaded & embedded successfully!`)
  } catch (err: any) {
    alert(`Upload failed: ${err.data?.detail || err.message || err}`)
  } finally {
    uploading.value = false
    target.value = '' // clear input
  }
}

const tokenEstimate = computed(() => {
  // Rough estimate of tokens: 4 characters per token
  return Math.ceil(text.value.length / 4)
})
</script>

<template>
  <div class="relative w-full">
    <!-- hidden file input -->
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      accept=".pdf,.docx,.txt,.md,.csv,.json"
      @change="handleFileChange"
    />

    <div class="relative w-full bg-white dark:bg-stone-900 rounded-2xl shadow-sm border border-stone-200/80 dark:border-stone-800/80 overflow-hidden flex flex-col transition-shadow duration-300 focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-500 dark:focus-within:border-blue-500">
      <textarea
        v-model="text"
        class="w-full h-20 p-4 resize-none bg-transparent border-0 outline-none text-stone-800 dark:text-stone-200 placeholder-stone-400 text-sm"
        placeholder="Ask a question or enter a command..."
        aria-label="Message input"
        @keydown="handleKeyDown"
      />
      <div class="flex items-center justify-between px-3 py-2 bg-stone-50/50 dark:bg-stone-900/50 border-t border-stone-100 dark:border-stone-800 text-xs">
        <!-- Live character/token metrics -->
        <span class="text-[10px] text-stone-400 font-mono pl-1">
          {{ text.length }} chars • ~{{ tokenEstimate }} tokens
        </span>

        <div class="flex items-center gap-2">
          <!-- Attach file -->
          <button
            :disabled="uploading"
            class="p-2 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 disabled:opacity-40 transition-colors"
            title="Upload document to RAG knowledge base"
            aria-label="Attach file"
            @click="triggerFileInput"
          >
            <Loader2 v-if="uploading" :size="16" class="animate-spin text-blue-500" />
            <Paperclip v-else :size="16" />
          </button>

          <!-- Stop Generation -->
          <button
            v-if="props.busy"
            class="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 hover:bg-red-200 text-red-600 dark:bg-red-950/40 dark:text-red-400 dark:hover:bg-red-900/40 shadow-sm transition-colors"
            title="Stop generation"
            aria-label="Stop generation"
            @click="emit('stop')"
          >
            <Square :size="14" :fill="'currentColor'" />
          </button>

          <!-- Send message -->
          <button
            v-else
            :disabled="!text.trim() || props.busy"
            class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:hover:bg-blue-600 text-white shadow-sm transition-colors"
            title="Send message"
            aria-label="Send message"
            @click="submit"
          >
            <ArrowUp :size="16" :stroke-width="2" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
