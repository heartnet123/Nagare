<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { Session } from '~/types'
import {
  Waves,
  Search,
  BarChart2,
  CheckCircle2,
  Activity,
  ChevronRight
} from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const api = useApi()
const recentSessions = ref<Session[]>([])

const showHistoryModal = ref(false)
const searchQuery = ref('')
const allSessions = ref<Session[]>([])
const loadingSessions = ref(false)

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

const fetchAllSessions = async (search = '') => {
  loadingSessions.value = true
  try {
    const res = await api.sessions.list(search)
    allSessions.value = res.sessions
  } catch (error) {
    console.error('Failed to load sessions:', error)
  } finally {
    loadingSessions.value = false
  }
}

watch(showHistoryModal, (val) => {
  if (val) {
    searchQuery.value = ''
    fetchAllSessions()
  }
})

let searchTimeout: ReturnType<typeof setTimeout> | undefined
watch(searchQuery, (newVal) => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchAllSessions(newVal)
  }, 150)
})

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
        <div class="text-blue-600 dark:text-blue-500 mb-6">
          <Waves
            :size="56"
            :stroke-width="1.5"
          />
        </div>
        <h1 class="text-4xl md:text-5xl font-semibold tracking-tight mb-3 text-stone-900 dark:text-stone-100">
          Good <span class="text-blue-600 dark:text-blue-500">morning</span>
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

      <!-- Recent Conversations Card List -->
      <div
        v-if="recentSessions.length > 0"
        class="mt-12 w-full bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-sm overflow-hidden"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-stone-200 dark:border-stone-800">
          <h2 class="text-sm font-semibold text-stone-900 dark:text-stone-100 tracking-tight">
            Recent Conversations
          </h2>
          <button
            type="button"
            class="text-xs font-semibold text-blue-600 dark:text-blue-500 hover:underline cursor-pointer focus:outline-none"
            @click="showHistoryModal = true"
          >
            View all
          </button>
        </div>

        <!-- List rows -->
        <div class="divide-y divide-stone-200 dark:divide-stone-800">
          <NuxtLink
            v-for="s in recentSessions"
            :key="s.id"
            :to="`/session/${s.id}`"
            class="flex items-center justify-between px-6 py-4 hover:bg-stone-50/50 dark:hover:bg-stone-800/20 transition-colors group"
          >
            <div class="flex flex-col min-w-0 pr-4">
              <span class="text-sm font-semibold text-stone-800 dark:text-stone-200 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {{ s.name }}
              </span>
              <span class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                {{ s.last_message_content || (s.rag ? 'Search query session' : (s.model ? `Chat via ${s.model}` : 'New session')) }}
              </span>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-xs text-stone-400 dark:text-stone-500">
                {{ formatRelativeTime(s.updated_at || s.created_at) }}
              </span>
              <ChevronRight
                :size="16"
                class="text-stone-400 dark:text-stone-500 group-hover:translate-x-0.5 transition-transform"
              />
            </div>
          </NuxtLink>
        </div>
      </div>

      <!-- Search Modal -->
      <UModal v-model:open="showHistoryModal">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-stone-900 dark:text-stone-100">
              All Conversations
            </h3>
          </div>
        </template>
        <template #body>
          <div class="flex flex-col gap-4">
            <!-- Search bar -->
            <div class="relative">
              <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-stone-400 dark:text-stone-500">
                <Search :size="16" />
              </span>
              <input
                v-model="searchQuery"
                type="text"
                class="w-full pl-10 pr-4 py-2 border border-stone-200 dark:border-stone-800 rounded-xl bg-stone-50 dark:bg-stone-900/50 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-stone-800 dark:text-stone-200"
                placeholder="Search conversations by name..."
              >
            </div>

            <!-- Scrollable List -->
            <div class="max-h-[50vh] overflow-y-auto divide-y divide-stone-100 dark:divide-stone-800 pr-1 select-none">
              <div
                v-if="loadingSessions && allSessions.length === 0"
                class="flex flex-col items-center justify-center py-8 text-stone-400"
              >
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2" />
                <span class="text-xs">Loading conversations...</span>
              </div>
              <div
                v-else-if="allSessions.length === 0"
                class="text-center py-8 text-stone-400 dark:text-stone-500 text-sm"
              >
                No conversations found.
              </div>
              <NuxtLink
                v-for="s in allSessions"
                :key="s.id"
                :to="`/session/${s.id}`"
                class="flex items-center justify-between py-3 px-2 rounded-xl hover:bg-stone-50/80 dark:hover:bg-stone-800/30 transition-colors group"
                @click="showHistoryModal = false"
              >
                <div class="flex flex-col min-w-0 pr-4">
                  <span class="text-sm font-semibold text-stone-800 dark:text-stone-200 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {{ s.name }}
                  </span>
                  <span class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                    {{ s.last_message_content || (s.rag ? 'Search query session' : (s.model ? `Chat via ${s.model}` : 'New session')) }}
                  </span>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                  <span class="text-xs text-stone-400 dark:text-stone-500">
                    {{ formatRelativeTime(s.updated_at || s.created_at) }}
                  </span>
                  <ChevronRight
                    :size="16"
                    class="text-stone-400 dark:text-stone-500 group-hover:translate-x-0.5 transition-transform"
                  />
                </div>
              </NuxtLink>
            </div>
          </div>
        </template>
      </UModal>
    </div>
  </div>
</template>
