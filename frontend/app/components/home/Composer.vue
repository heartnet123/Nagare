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
      }
    }) as { id: string }

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

<template>
  <div class="relative w-full mb-8 group">
    <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
    <div class="relative w-full bg-white rounded-2xl shadow-sm border border-stone-200/80 overflow-hidden flex flex-col transition-shadow duration-300 focus-within:ring-4 focus-within:ring-blue-50 focus-within:border-blue-300">
      <textarea
        v-model="value"
        class="w-full h-32 p-5 resize-none bg-transparent outline-none text-stone-800 text-lg placeholder-stone-400"
        placeholder="Ask anything"
        aria-label="Message input"
        @keydown="handleKeyDown"
      />
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
            aria-label="Chat Mode"
            @click="mode = 'chat'"
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
            aria-label="Agent Mode"
            @click="mode = 'agent'"
          >
            Agent
          </button>
        </div>

        <button
          class="p-2 text-stone-400 hover:text-stone-600 transition-colors"
          aria-label="Attach file"
        >
          <Paperclip
            :size="20"
            :stroke-width="1.5"
          />
        </button>
        <button
          class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-wait text-white shadow-sm transition-colors"
          aria-label="Send message"
          :disabled="creating"
          @click="submit"
        >
          <Loader2
            v-if="creating"
            :size="20"
            class="animate-spin"
          />
          <ArrowUp
            v-else
            :size="20"
            :stroke-width="2"
          />
        </button>
      </div>
    </div>
  </div>
</template>
