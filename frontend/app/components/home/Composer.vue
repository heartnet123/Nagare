<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from '#app'
import { Paperclip, ArrowUp } from '@lucide/vue'

const value = ref('')
const router = useRouter()

const submit = () => {
  const text = value.value.trim()
  if (!text) return
  router.push(`/chat?q=${encodeURIComponent(text)}`)
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    if (e.isComposing) return
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
          class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors"
          aria-label="Send message"
          @click="submit"
        >
          <ArrowUp
            :size="20"
            :stroke-width="2"
          />
        </button>
      </div>
    </div>
  </div>
</template>
