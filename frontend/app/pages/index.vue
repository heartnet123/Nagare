<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Session } from '~/types'
import {
  Waves,
  Search,
  BarChart2,
  CheckCircle2,
  Activity,
  Sparkles,
  Bot,
  ArrowRight,
  MessageSquare,
  Clock
} from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const api = useApi()
const recentSessions = ref<Session[]>([])

const formatRelativeTime = (dateStr: string | null | undefined) => {
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

onMounted(async () => {
  try {
    const res = await api.sessions.list()
    // Show up to 3 most recent active sessions
    recentSessions.value = res.sessions.slice(0, 3)
  } catch (error) {
    console.error('Failed to load recent sessions:', error)
  }
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-6 pb-12 hide-scrollbar flex items-center justify-center">
    <div class="max-w-3xl mx-auto w-full">
      <!-- Hero -->
      <div class="flex flex-col items-center justify-center mb-8">
        <div class="text-blue-600 mb-6 animate-pulse">
          <Waves
            :size="56"
            :stroke-width="1.5"
          />
        </div>
        <h1 class="text-4xl md:text-5xl font-semibold tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
          Good morning
        </h1>
        <p class="text-lg md:text-xl text-stone-500 dark:text-stone-400 font-medium">
          How can I help you today?
        </p>
      </div>

      <HomeComposer />

      <!-- Action chips -->
      <div class="flex flex-wrap items-center justify-center gap-3 mb-12">
        <NuxtLink
          to="/knowledge"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/60 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800/80 hover:border-stone-300 dark:hover:border-stone-700 shadow-sm transition-all"
        >
          <Search
            :size="16"
            :stroke-width="1.5"
          />
          Search Knowledge
        </NuxtLink>
        <NuxtLink
          to="/analytics"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/60 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800/80 hover:border-stone-300 dark:hover:border-stone-700 shadow-sm transition-all"
        >
          <BarChart2
            :size="16"
            :stroke-width="1.5"
          />
          Analyze Data
        </NuxtLink>
        <NuxtLink
          to="/evaluations"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/60 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800/80 hover:border-stone-300 dark:hover:border-stone-700 shadow-sm transition-all"
        >
          <CheckCircle2
            :size="16"
            :stroke-width="1.5"
          />
          Evaluate Response
        </NuxtLink>
        <NuxtLink
          to="/monitoring"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/60 text-sm font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800/80 hover:border-stone-300 dark:hover:border-stone-700 shadow-sm transition-all"
        >
          <Activity
            :size="16"
            :stroke-width="1.5"
          />
          System Status
        </NuxtLink>
      </div>

      <!-- Recent Conversations -->
      <div v-if="recentSessions.length > 0" class="mt-8 border-t border-stone-200 dark:border-stone-800 pt-8 w-full">
        <h2 class="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-4 flex items-center gap-2 tracking-wide uppercase">
          <Clock :size="14" class="text-stone-400" />
          Recent Conversations
        </h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <NuxtLink
            v-for="s in recentSessions"
            :key="s.id"
            :to="`/chat?session=${s.id}`"
            class="flex flex-col p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/40 hover:border-blue-500 dark:hover:border-blue-500/80 hover:shadow-sm transition-all text-left group"
          >
            <div class="flex items-center gap-2 mb-2 text-stone-400 dark:text-stone-500 text-xs">
              <MessageSquare :size="13" class="group-hover:text-blue-500 transition-colors" />
              <span class="truncate font-medium max-w-[150px]">{{ s.model || 'AI Chat' }}</span>
            </div>
            <h3 class="text-sm font-semibold text-stone-800 dark:text-stone-200 truncate mb-1">
              {{ s.name }}
            </h3>
            <span class="text-[10px] text-stone-400 dark:text-stone-500 mt-2">
              Updated {{ formatRelativeTime(s.updated_at || s.created_at) }}
            </span>
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
