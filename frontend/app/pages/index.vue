<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Search,
  Bell,
  Paperclip,
  Play,
  Plug,
  Bot,
  Folder,
  CheckCircle2,
  Trophy,
  Lightbulb,
  MessageSquare,
  Sparkles,
  ChevronRight,
  Database,
  FileText,
  BarChart2,
  SlidersHorizontal,
  ChevronDown,
  ArrowRight,
  Loader2,
  Cpu
} from '@lucide/vue'
import type { Session } from '~/types'
import { useApiSessions } from '~/composables/useApi/sessions'
import { useApiMcp } from '~/composables/useApi/mcp'
import { useApiAgents } from '~/composables/useApi/agents'
import { useApiEvaluations } from '~/composables/useApi/evaluations'
import { useApiMonitoring } from '~/composables/useApi/monitoring'

definePageMeta({
  layout: 'default'
})

const sessionsApi = useApiSessions()
const mcpApi = useApiMcp()
const agentsApi = useApiAgents()
const evaluationsApi = useApiEvaluations()
const monitoringApi = useApiMonitoring()
const { activeModelName } = useActiveSelection()

// State
const goalText = ref('')
const goalTextarea = ref<HTMLTextAreaElement | null>(null)
const submittingGoal = ref(false)
const composerMode = ref<'chat' | 'agent'>('agent')
const showToolsDropdown = ref(false)
const showSearchModal = ref(false)
const searchQuery = ref('')

// Dynamic backend data
const activeSessions = ref<Session[]>([])
const completedSessions = ref<Session[]>([])
const allSessions = ref<Session[]>([])
const mcpServers = ref<any[]>([])
const agents = ref<any[]>([])
const evaluations = ref<any[]>([])
const avgLatency = ref<string>('—')
const loading = ref(true)

// Formatted date: "Mon, Apr 28, 2025"
const formattedDate = computed(() => {
  const d = new Date()
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
})

// Relative time formatter
const formatRelativeTime = (dateStr: string | null | undefined) => {
  if (!dateStr) return 'Recently'
  try {
    const cleanStr = dateStr.replace(' ', 'T')
    const d = new Date(cleanStr)
    if (isNaN(d.getTime())) return dateStr
    const diffMs = Date.now() - d.getTime()
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

// Onboarding steps completion calculation
const step1Complete = computed(() => mcpServers.value.length > 0)
const step2Complete = computed(() => allSessions.value.length > 0)
const step3Complete = computed(() => agents.value.length > 0)
const step4Complete = computed(() => evaluations.value.length > 0)

const completedStepsCount = computed(() =>
  [step1Complete.value, step2Complete.value, step3Complete.value, step4Complete.value].filter(Boolean).length
)

// Load data from backend
const loadDashboardData = async () => {
  loading.value = true
  try {
    const [sessRes, mcpRes, agentsRes, evalsRes, healthRes] = await Promise.allSettled([
      sessionsApi.list(),
      mcpApi.list(),
      agentsApi.list(),
      evaluationsApi.list(),
      monitoringApi.getMetrics()
    ])

    if (sessRes.status === 'fulfilled' && sessRes.value?.sessions) {
      const list = sessRes.value.sessions
      allSessions.value = list
      activeSessions.value = list.filter((s: Session) => !s.archived).slice(0, 5)
      completedSessions.value = list.filter((s: Session) => s.archived).slice(0, 5)
    }

    if (mcpRes.status === 'fulfilled' && Array.isArray(mcpRes.value)) {
      mcpServers.value = mcpRes.value
    }

    if (agentsRes.status === 'fulfilled' && Array.isArray(agentsRes.value)) {
      agents.value = agentsRes.value
    }

    if (evalsRes.status === 'fulfilled' && Array.isArray(evalsRes.value)) {
      evaluations.value = evalsRes.value
    }

    if (healthRes.status === 'fulfilled' && healthRes.value?.latency) {
      avgLatency.value = `${Math.round(healthRes.value.latency)}ms`
    }
  } catch (err) {
    console.error('Failed to load dashboard data:', err)
  } finally {
    loading.value = false
  }
}

// Actions
const focusGoalInput = () => {
  if (goalTextarea.value) {
    goalTextarea.value.focus()
    goalTextarea.value.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

const startFirstTask = async () => {
  const text = goalText.value.trim()
  if (!text || submittingGoal.value) return

  submittingGoal.value = true
  try {
    const session = await $fetch<{ id: string }>('/api/session', {
      method: 'POST',
      body: {
        name: text.length > 48 ? `${text.slice(0, 45)}...` : text,
        mode: composerMode.value,
        model: activeModelName.value || undefined
      }
    })

    await navigateTo(`/session/${session.id}?q=${encodeURIComponent(text)}`)
    goalText.value = ''
  } catch (error) {
    console.error('Failed to start task:', error)
  } finally {
    submittingGoal.value = false
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    startFirstTask()
  }
}

// Global shortcut for search modal Cmd/Ctrl + K
const handleGlobalKeydown = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    showSearchModal.value = !showSearchModal.value
  }
}

// Filtered sessions in search modal
const filteredSessions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return allSessions.value.slice(0, 8)
  return allSessions.value.filter((s: Session) =>
    s.name.toLowerCase().includes(q) ||
    (s.last_message_content && s.last_message_content.toLowerCase().includes(q))
  ).slice(0, 10)
})

onMounted(() => {
  loadDashboardData()
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-6 py-8 hide-scrollbar">
    <div class="max-w-[1440px] mx-auto flex flex-col lg:flex-row gap-8 items-start">
      <!-- Main Content Column -->
      <div class="flex-1 min-w-0 w-full space-y-8">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 border-b border-stone-100 dark:border-stone-800 pb-5">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100 font-sans">
              Your workspace
            </h1>
            <p class="text-sm font-medium text-stone-500 dark:text-stone-400 mt-1">
              Set a goal. Follow the work. Review the result.
            </p>
          </div>
          <div class="text-left sm:text-right shrink-0">
            <p class="text-sm font-semibold text-stone-800 dark:text-stone-200">
              {{ formattedDate }}
            </p>
            <p class="text-xs text-stone-400 dark:text-stone-500">
              A calmer, more productive day.
            </p>
          </div>
        </div>

        <!-- Goal Banner / Composer -->
        <div class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-50/90 via-sky-50/50 to-white dark:from-blue-950/20 dark:via-stone-900 dark:to-stone-900 border border-blue-100/80 dark:border-stone-800 p-6 md:p-8 shadow-sm">
          <!-- Decorative Background Asset -->
          <div class="absolute right-0 top-0 w-80 h-full pointer-events-none opacity-40 dark:opacity-20 hidden md:block overflow-hidden">
            <img
              src="/hero-banner.jpg"
              alt="Decorative"
              class="w-full h-full object-cover object-left mask-radial"
            >
          </div>

          <div class="relative z-10 max-w-2xl">
            <span class="inline-block text-xs font-semibold tracking-wide text-blue-600 dark:text-blue-400 uppercase mb-2">
              Welcome to NagareOS.
            </span>
            <h2 class="text-2xl md:text-3xl font-bold text-stone-900 dark:text-stone-100 tracking-tight leading-snug mb-6">
              Start with a goal and your workspace will begin to fill itself.
            </h2>

            <!-- Composer Input Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl border border-stone-200/90 dark:border-stone-750 shadow-sm p-4 transition-all focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500">
              <textarea
                ref="goalTextarea"
                v-model="goalText"
                rows="3"
                placeholder="What would you like to accomplish?"
                class="w-full resize-none bg-transparent outline-none text-stone-800 dark:text-stone-200 placeholder-stone-400 text-base leading-relaxed"
                :disabled="submittingGoal"
                @keydown="handleKeyDown"
              />

              <!-- Actions Bar -->
              <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-stone-100 dark:border-stone-800">
                <div class="flex items-center gap-2">

                  <!-- Tools Dropdown -->
                  <div class="relative">
                    <button
                      type="button"
                      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
                      @click="showToolsDropdown = !showToolsDropdown"
                    >
                      <SlidersHorizontal :size="14" />
                      <span>Tools</span>
                      <ChevronDown
                        :size="13"
                        class="text-stone-400 transition-transform duration-150"
                        :class="{ 'rotate-180': showToolsDropdown }"
                      />
                    </button>

                    <!-- Tools Menu -->
                    <div
                      v-if="showToolsDropdown"
                      class="absolute left-0 bottom-full mb-2 w-56 rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-lg p-2 z-50 text-xs"
                    >
                      <div class="px-2 py-1 font-semibold text-stone-400 text-[10px] uppercase tracking-wider">
                        Configured Tools
                      </div>
                      <div
                        v-if="mcpServers.length === 0"
                        class="px-2 py-2 text-stone-400"
                      >
                        No external tools linked.
                        <NuxtLink
                          to="/mcp"
                          class="text-blue-600 hover:underline block mt-1"
                        >
                          Configure MCP &rarr;
                        </NuxtLink>
                      </div>
                      <NuxtLink
                        v-for="server in mcpServers"
                        :key="server.name || server.id"
                        to="/mcp"
                        class="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-stone-100 dark:hover:bg-stone-800 text-left text-stone-700 dark:text-stone-300"
                        @click="showToolsDropdown = false"
                      >
                        <Cpu :size="13" />
                        <span class="truncate">{{ server.name }}</span>
                      </NuxtLink>
                    </div>
                  </div>

                  <!-- Mode Switcher -->
                  <div class="hidden sm:flex items-center bg-stone-100 dark:bg-stone-800 rounded-lg p-0.5 text-xs font-medium">
                    <button
                      type="button"
                      class="px-2.5 py-1 rounded-md transition-all"
                      :class="composerMode === 'agent' ? 'bg-white dark:bg-stone-700 text-blue-600 dark:text-blue-400 shadow-sm font-semibold' : 'text-stone-500'"
                      @click="composerMode = 'agent'"
                    >
                      Agent
                    </button>
                    <button
                      type="button"
                      class="px-2.5 py-1 rounded-md transition-all"
                      :class="composerMode === 'chat' ? 'bg-white dark:bg-stone-700 text-blue-600 dark:text-blue-400 shadow-sm font-semibold' : 'text-stone-500'"
                      @click="composerMode = 'chat'"
                    >
                      Chat
                    </button>
                  </div>
                </div>

                <!-- Submit Button -->
                <button
                  type="button"
                  class="flex items-center gap-2 px-5 py-2 rounded-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-sm font-semibold shadow-sm shadow-blue-500/20 disabled:opacity-50 transition-all cursor-pointer"
                  :disabled="!goalText.trim() || submittingGoal"
                  @click="startFirstTask"
                >
                  <Loader2
                    v-if="submittingGoal"
                    :size="15"
                    class="animate-spin"
                  />
                  <Play
                    v-else
                    :size="14"
                    class="fill-current"
                  />
                  <span>Start first task</span>
                </button>
              </div>
            </div>

            <!-- Quick Action Links -->
            <div class="flex flex-wrap items-center gap-3">
              <NuxtLink
                to="/mcp"
                class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-stone-850/80 hover:bg-white dark:hover:bg-stone-800 border border-blue-100 dark:border-stone-800 text-xs font-semibold text-stone-700 dark:text-stone-300 shadow-2xs transition-colors"
              >
                <Plug
                  :size="13"
                  class="text-blue-500"
                />
                <span>Connect tools</span>
                <ChevronRight
                  :size="13"
                  class="text-stone-400"
                />
              </NuxtLink>

              <NuxtLink
                to="/agents"
                class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-stone-850/80 hover:bg-white dark:hover:bg-stone-800 border border-blue-100 dark:border-stone-800 text-xs font-semibold text-stone-700 dark:text-stone-300 shadow-2xs transition-colors"
              >
                <Bot
                  :size="13"
                  class="text-blue-500"
                />
                <span>Explore agents</span>
                <ChevronRight
                  :size="13"
                  class="text-stone-400"
                />
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- 4 Step Onboarding Guide Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <!-- Step 1 -->
          <NuxtLink
            to="/mcp"
            class="group p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-xs hover:border-blue-300 dark:hover:border-blue-800 transition-all flex flex-col justify-between min-h-[140px]"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold text-xs flex items-center justify-center">
                  1
                </span>
                <CheckCircle2
                  v-if="step1Complete"
                  :size="16"
                  class="text-blue-600"
                />
              </div>
              <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors">
                Connect your tools
              </h3>
              <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                Link Slack, Notion, Drive and more.
              </p>
            </div>
            <div class="mt-4 text-stone-400 group-hover:text-blue-500 transition-colors">
              <Database :size="18" />
            </div>
          </NuxtLink>

          <!-- Step 2 -->
          <button
            type="button"
            class="group p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-xs hover:border-blue-300 dark:hover:border-blue-800 transition-all flex flex-col justify-between text-left min-h-[140px]"
            @click="focusGoalInput"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <CheckCircle2
                  v-if="step2Complete"
                  :size="16"
                  class="text-blue-600"
                />
              </div>
              <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors">
                Create your first task
              </h3>
              <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                Describe what you want to accomplish.
              </p>
            </div>
            <div class="mt-4 text-stone-400 group-hover:text-blue-500 transition-colors">
              <FileText :size="18" />
            </div>
          </button>

          <!-- Step 3 -->
          <NuxtLink
            to="/agents"
            class="group p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-xs hover:border-blue-300 dark:hover:border-blue-800 transition-all flex flex-col justify-between min-h-[140px]"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <CheckCircle2
                  v-if="step3Complete"
                  :size="16"
                  class="text-blue-600"
                />
              </div>
              <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors">
                Assign an agent
              </h3>
              <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                Let an AI agent handle the work for you.
              </p>
            </div>
            <div class="mt-4 text-stone-400 group-hover:text-blue-500 transition-colors">
              <Bot :size="18" />
            </div>
          </NuxtLink>

          <!-- Step 4 -->
          <NuxtLink
            to="/evaluations"
            class="group p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-xs hover:border-blue-300 dark:hover:border-blue-800 transition-all flex flex-col justify-between min-h-[140px]"
          >
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-bold text-xs flex items-center justify-center">
                  4
                </span>
                <CheckCircle2
                  v-if="step4Complete"
                  :size="16"
                  class="text-blue-600"
                />
              </div>
              <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors">
                Review your first result
              </h3>
              <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                Get back polished results, ready to use.
              </p>
            </div>
            <div class="mt-4 text-stone-400 group-hover:text-blue-500 transition-colors">
              <BarChart2 :size="18" />
            </div>
          </NuxtLink>
        </div>

        <!-- Section 1: Active Work -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-stone-900 dark:text-stone-100 tracking-tight">
              Active work
            </h2>
            <button
              type="button"
              class="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 cursor-pointer"
              @click="showSearchModal = true"
            >
              <span>View all</span>
              <ArrowRight :size="13" />
            </button>
          </div>

          <!-- Empty State -->
          <div
            v-if="activeSessions.length === 0"
            class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center"
          >
            <div class="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3">
              <Folder :size="22" />
            </div>
            <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 mb-1">
              No active work yet
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm mb-4">
              Create your first task to start collaborating with agents.
            </p>
            <button
              type="button"
              class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors"
              @click="focusGoalInput"
            >
              Create task
            </button>
          </div>

          <!-- Populated State -->
          <div
            v-else
            class="divide-y divide-stone-100 dark:divide-stone-800 rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 overflow-hidden"
          >
            <NuxtLink
              v-for="s in activeSessions"
              :key="s.id"
              :to="`/session/${s.id}`"
              class="flex items-center justify-between p-4 hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors group"
            >
              <div class="flex items-center gap-3.5 min-w-0 pr-4">
                <div class="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                  <Folder :size="18" />
                </div>
                <div class="min-w-0">
                  <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100 truncate group-hover:text-blue-600 transition-colors">
                    {{ s.name }}
                  </h4>
                  <p class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                    {{ s.last_message_content || 'Session initialized' }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-xs text-stone-400">
                  {{ formatRelativeTime(s.updated_at || s.created_at) }}
                </span>
                <ChevronRight
                  :size="15"
                  class="text-stone-400 group-hover:translate-x-0.5 transition-transform"
                />
              </div>
            </NuxtLink>
          </div>
        </div>

        <!-- Section 2: Needs Your Decision -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-stone-900 dark:text-stone-100 tracking-tight">
              Needs your decision
            </h2>
            <NuxtLink
              to="/logs"
              class="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight :size="13" />
            </NuxtLink>
          </div>

          <!-- Empty State -->
          <div class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center">
            <div class="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3">
              <CheckCircle2 :size="22" />
            </div>
            <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 mb-1">
              No decisions pending
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm">
              Approvals and questions from agents will appear here.
            </p>
          </div>
        </div>

        <!-- Section 3: Recently Completed -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-stone-900 dark:text-stone-100 tracking-tight">
              Recently completed
            </h2>
            <button
              type="button"
              class="text-xs font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 cursor-pointer"
              @click="showSearchModal = true"
            >
              <span>View all</span>
              <ArrowRight :size="13" />
            </button>
          </div>

          <!-- Empty State -->
          <div
            v-if="completedSessions.length === 0"
            class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center"
          >
            <div class="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-3">
              <Trophy :size="22" />
            </div>
            <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100 mb-1">
              Nothing completed yet
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm">
              Finished work will show up here once your agents deliver results.
            </p>
          </div>

          <!-- Populated State -->
          <div
            v-else
            class="divide-y divide-stone-100 dark:divide-stone-800 rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 overflow-hidden"
          >
            <NuxtLink
              v-for="s in completedSessions"
              :key="s.id"
              :to="`/session/${s.id}`"
              class="flex items-center justify-between p-4 hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors group"
            >
              <div class="flex items-center gap-3.5 min-w-0 pr-4">
                <div class="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                  <Trophy :size="18" />
                </div>
                <div class="min-w-0">
                  <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100 truncate group-hover:text-blue-600 transition-colors">
                    {{ s.name }}
                  </h4>
                  <p class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                    {{ s.last_message_content || 'Completed task' }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-xs text-stone-400">
                  {{ formatRelativeTime(s.updated_at || s.created_at) }}
                </span>
                <ChevronRight
                  :size="15"
                  class="text-stone-400 group-hover:translate-x-0.5 transition-transform"
                />
              </div>
            </NuxtLink>
          </div>
        </div>
      </div>

      <!-- Right Column: Getting Started, Stats & Tips -->
      <div class="w-full lg:w-80 xl:w-88 shrink-0 space-y-6">
        <!-- Top Search Bar & Notification -->
        <div class="flex items-center gap-3">
          <div
            class="flex-1 flex items-center justify-between px-3.5 py-2 rounded-xl bg-white dark:bg-stone-900 border border-stone-200/90 dark:border-stone-800 shadow-2xs cursor-pointer hover:border-blue-400 transition-colors"
            @click="showSearchModal = true"
          >
            <div class="flex items-center gap-2 text-stone-400 text-xs">
              <Search :size="15" />
              <span>Search anything...</span>
            </div>
            <kbd class="px-1.5 py-0.5 text-[10px] font-medium bg-stone-100 dark:bg-stone-800 text-stone-500 dark:text-stone-400 rounded border border-stone-200 dark:border-stone-700">
              ⌘K
            </kbd>
          </div>

          <button
            type="button"
            class="relative p-2.5 rounded-xl bg-white dark:bg-stone-900 border border-stone-200/90 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 shadow-2xs transition-colors"
            aria-label="Notifications"
            @click="navigateTo('/logs')"
          >
            <Bell :size="17" />
            <span class="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-stone-900" />
          </button>
        </div>

        <!-- Getting Started Progress Card -->
        <div class="rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 p-5 shadow-xs space-y-4">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-stone-900 dark:text-stone-100">
              Getting started
            </h3>
            <span class="text-xs font-semibold text-stone-500 dark:text-stone-400">
              {{ completedStepsCount }}/4 complete
            </span>
          </div>

          <!-- Steps Stepper -->
          <div class="space-y-3">
            <!-- Item 1 -->
            <NuxtLink
              to="/mcp"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors"
                  :class="step1Complete ? 'bg-blue-600 text-white' : 'bg-blue-50 dark:bg-blue-950/40 text-blue-600'"
                >
                  1
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors truncate">
                    Connect your tools
                  </p>
                  <p class="text-[11px] text-stone-400 truncate">
                    Link your favorite apps
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-blue-600 shrink-0"
              />
            </NuxtLink>

            <!-- Item 2 -->
            <button
              type="button"
              class="w-full flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors text-left group"
              @click="focusGoalInput"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                  :class="step2Complete ? 'bg-blue-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  2
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors truncate">
                    Create your first task
                  </p>
                  <p class="text-[11px] text-stone-400 truncate">
                    Turn an idea into action
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-blue-600 shrink-0"
              />
            </button>

            <!-- Item 3 -->
            <NuxtLink
              to="/agents"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                  :class="step3Complete ? 'bg-blue-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  3
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors truncate">
                    Assign an agent
                  </p>
                  <p class="text-[11px] text-stone-400 truncate">
                    Let AI do the work for you
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-blue-600 shrink-0"
              />
            </NuxtLink>

            <!-- Item 4 -->
            <NuxtLink
              to="/evaluations"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 transition-colors group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                  :class="step4Complete ? 'bg-blue-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  4
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-bold text-stone-900 dark:text-stone-100 group-hover:text-blue-600 transition-colors truncate">
                    Review your first result
                  </p>
                  <p class="text-[11px] text-stone-400 truncate">
                    See what your agents deliver
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-blue-600 shrink-0"
              />
            </NuxtLink>
          </div>
        </div>

        <!-- 2x2 Metric Stat Cards -->
        <div class="grid grid-cols-2 gap-3">
          <!-- Active tasks -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-bold text-stone-900 dark:text-stone-100">
                {{ activeSessions.length }}
              </span>
              <!-- Sparkline SVG -->
              <svg
                class="w-10 h-5 text-blue-500"
                viewBox="0 0 40 20"
                fill="none"
              >
                <path
                  d="M2 15 Q 12 5, 22 12 T 38 4"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  fill="none"
                />
              </svg>
            </div>
            <p class="text-[11px] font-medium text-stone-500 dark:text-stone-400 mt-2">
              Active tasks
            </p>
          </div>

          <!-- Results -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-bold text-stone-900 dark:text-stone-100">
                {{ evaluations.length }}
              </span>
              <div class="flex items-end gap-0.5 h-5 text-blue-500">
                <div class="w-1 bg-current h-2 rounded-t" />
                <div class="w-1 bg-current h-4 rounded-t" />
                <div class="w-1 bg-current h-3 rounded-t" />
                <div class="w-1 bg-current h-5 rounded-t" />
              </div>
            </div>
            <p class="text-[11px] font-medium text-stone-500 dark:text-stone-400 mt-2">
              Results
            </p>
          </div>

          <!-- Decisions pending -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-bold text-stone-900 dark:text-stone-100">
                0
              </span>
              <!-- Orange sparkline SVG -->
              <svg
                class="w-10 h-5 text-amber-500"
                viewBox="0 0 40 20"
                fill="none"
              >
                <path
                  d="M2 16 Q 15 10, 25 15 T 38 6"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  fill="none"
                />
              </svg>
            </div>
            <p class="text-[11px] font-medium text-stone-500 dark:text-stone-400 mt-2">
              Decisions pending
            </p>
          </div>

          <!-- Avg. completion time -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-bold text-stone-900 dark:text-stone-100">
                {{ avgLatency }}
              </span>
              <!-- Green trend SVG -->
              <svg
                class="w-10 h-5 text-emerald-500"
                viewBox="0 0 40 20"
                fill="none"
              >
                <path
                  d="M2 17 L 15 12 L 25 14 L 38 5"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <p class="text-[11px] font-medium text-stone-500 dark:text-stone-400 mt-2">
              Avg. latency
            </p>
          </div>
        </div>

        <!-- Tips Card -->
        <div class="rounded-2xl bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 p-5 shadow-xs space-y-4">
          <div class="flex items-center gap-2 text-stone-900 dark:text-stone-100">
            <Lightbulb
              :size="16"
              class="text-amber-500"
            />
            <h3 class="text-sm font-bold">
              Tips
            </h3>
          </div>

          <div class="space-y-3.5">
            <!-- Tip 1 -->
            <div class="flex items-start gap-3 text-xs">
              <Plug
                :size="15"
                class="text-blue-500 shrink-0 mt-0.5"
              />
              <div>
                <h4 class="font-bold text-stone-800 dark:text-stone-200">
                  Connect Slack, Notion, or Drive
                </h4>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  Give your agents the context they need.
                </p>
              </div>
            </div>

            <!-- Tip 2 -->
            <div class="flex items-start gap-3 text-xs">
              <MessageSquare
                :size="15"
                class="text-blue-500 shrink-0 mt-0.5"
              />
              <div>
                <h4 class="font-bold text-stone-800 dark:text-stone-200">
                  Describe your goal in plain language
                </h4>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  You don't need to be specific or technical.
                </p>
              </div>
            </div>

            <!-- Tip 3 -->
            <div class="flex items-start gap-3 text-xs">
              <Sparkles
                :size="15"
                class="text-blue-500 shrink-0 mt-0.5"
              />
              <div>
                <h4 class="font-bold text-stone-800 dark:text-stone-200">
                  Agents will organize work automatically
                </h4>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  They break it down, take action, and keep you updated.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Search Modal / Global Command Palette -->
    <UModal v-model:open="showSearchModal">
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-stone-900 dark:text-stone-100">
            Search Workspace
          </h3>
        </div>
      </template>

      <template #body>
        <div class="space-y-4">
          <div class="relative">
            <span class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-stone-400">
              <Search :size="16" />
            </span>
            <input
              v-model="searchQuery"
              type="text"
              class="w-full pl-10 pr-4 py-2.5 border border-stone-200 dark:border-stone-800 rounded-xl bg-stone-50 dark:bg-stone-900/50 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-stone-800 dark:text-stone-200"
              placeholder="Search tasks, sessions or knowledge..."
              autofocus
            >
          </div>

          <!-- Results -->
          <div class="max-h-[50vh] overflow-y-auto divide-y divide-stone-100 dark:divide-stone-800">
            <div
              v-if="filteredSessions.length === 0"
              class="text-center py-6 text-stone-400 text-xs"
            >
              No items matching "{{ searchQuery }}".
            </div>
            <NuxtLink
              v-for="s in filteredSessions"
              :key="s.id"
              :to="`/session/${s.id}`"
              class="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors group"
              @click="showSearchModal = false"
            >
              <div class="min-w-0 pr-3">
                <h4 class="text-sm font-medium text-stone-800 dark:text-stone-200 truncate group-hover:text-blue-600 transition-colors">
                  {{ s.name }}
                </h4>
                <p class="text-xs text-stone-400 truncate mt-0.5">
                  {{ s.last_message_content || 'Session' }}
                </p>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:translate-x-0.5 transition-transform shrink-0"
              />
            </NuxtLink>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<style scoped>
.mask-radial {
  mask-image: radial-gradient(circle at 80% 50%, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(circle at 80% 50%, black 30%, transparent 80%);
}
</style>
