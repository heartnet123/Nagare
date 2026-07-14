<script setup lang="ts">
import { ref } from 'vue'
import { Paperclip, ArrowUp, Loader2, AlertCircle, X } from '@lucide/vue'

const value = ref('')
const creating = ref(false)
const mode = useState<'chat' | 'agent'>('composer-mode', () => 'chat')
const errorMsg = ref<string | null>(null)
const { activeModelName } = useActiveSelection()

const submit = async () => {
  const text = value.value.trim()
  if (!text || creating.value) return

  creating.value = true
  errorMsg.value = null
  try {
    const config = useRuntimeConfig()
    // Create a new session via the backend API
    const session = await $fetch('/api/session', {
      method: 'POST',
      baseURL: config.public.apiBase,
      body: {
        name: text.length > 48 ? `${text.slice(0, 45)}...` : text,
        mode: mode.value,
        model: activeModelName.value || undefined
      }
    }) as { id: string }

    // Redirect to the dedicated session page with the initial query
    await navigateTo(`/session/${session.id}?q=${encodeURIComponent(text)}`)
    value.value = ''
  } catch (error) {
    console.error('Failed to create session:', error)
    errorMsg.value = 'Failed to start session. Please try again.'
  } finally {
    creating.value = false
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    if (e.isComposing || creating.value) return
    submit()
  }
}
</script>

<template>
  <div class="relative w-full mb-8 group">
    <div class="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-sky-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-500" />
    <div class="relative w-full bg-white dark:bg-stone-900 rounded-2xl shadow-sm border border-stone-200/80 dark:border-stone-800 flex flex-col transition-shadow duration-300 focus-within:ring-4 focus-within:ring-blue-50 dark:focus-within:ring-blue-950/20 focus-within:border-blue-500">
      <textarea
        v-model="value"
        :readonly="creating"
        class="w-full h-32 p-5 resize-none bg-transparent outline-none text-stone-800 dark:text-stone-200 text-lg placeholder-stone-400 dark:placeholder-stone-500 rounded-t-2xl"
        placeholder="Ask anything..."
        aria-label="Message input"
        @keydown="handleKeyDown"
      />

      <div
        v-if="errorMsg"
        class="mx-5 mb-3 flex items-center justify-between p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm"
      >
        <div class="flex items-center gap-2">
          <AlertCircle class="h-4 w-4 shrink-0 text-red-500" />
          <span>{{ errorMsg }}</span>
        </div>
        <button
          type="button"
          class="p-1 hover:bg-red-100 rounded-md transition-colors text-red-500 hover:text-red-700"
          aria-label="Dismiss error"
          @click="errorMsg = null"
        >
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="flex items-center justify-end px-4 py-3 gap-3 bg-white dark:bg-stone-900 rounded-b-2xl">
        <div class="mr-auto bg-stone-100 dark:bg-stone-800 rounded-lg p-1 flex items-center gap-1">
          <button
            class="px-3 py-1 text-sm font-medium rounded-md transition-all"
            :class="[
              mode === 'chat'
                ? 'bg-white dark:bg-stone-700 shadow-sm text-blue-600 dark:text-blue-400 font-semibold'
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
                ? 'bg-white dark:bg-stone-700 shadow-sm text-blue-600 dark:text-blue-400 font-semibold'
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
          class="p-2 text-stone-400 hover:text-stone-600 dark:hover:text-stone-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="creating"
          aria-label="Attach file"
        >
          <Paperclip
            :size="20"
            :stroke-width="1.5"
          />
        </button>

        <!-- Model/Agent Selection Dropdown -->
        <WorkspaceDropdown />

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
