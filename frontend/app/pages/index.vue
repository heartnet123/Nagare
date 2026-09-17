<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Search,
  Bell,
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
  BarChart2,
  SlidersHorizontal,
  ChevronDown,
  ArrowRight,
  Loader2,
  Cpu,
  X
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
const toolsDropdownRef = ref<HTMLElement | null>(null)
const showSearchModal = ref(false)
const searchQuery = ref('')

// Dynamic backend data
const activeSessions = ref<Session[]>([])
const completedSessions = ref<Session[]>([])
const allSessions = ref<Session[]>([])
const mcpServers = ref<Awaited<ReturnType<typeof mcpApi.list>>>([])
const agents = ref<Awaited<ReturnType<typeof agentsApi.list>>>([])
const evaluations = ref<unknown[]>([])
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

const handleClickOutside = (e: MouseEvent) => {
  if (toolsDropdownRef.value && !toolsDropdownRef.value.contains(e.target as Node)) {
    showToolsDropdown.value = false
  }
}

// Filtered sessions in search modal
const filteredSessions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return allSessions.value.slice(0, 8)
  return allSessions.value.filter((s: Session) =>
    s.name.toLowerCase().includes(q)
    || (s.last_message_content && s.last_message_content.toLowerCase().includes(q))
  ).slice(0, 10)
})

onMounted(() => {
  loadDashboardData()
  window.addEventListener('keydown', handleGlobalKeydown)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-6 py-8">
    <div class="max-w-6xl mx-auto flex flex-col lg:flex-row gap-8 items-start">
      <!-- Main Content Column -->
      <div class="flex-1 min-w-0 w-full space-y-8">
        <!-- Header -->
        <header class="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 pb-2">
          <div>
            <h1 class="text-3xl font-semibold tracking-tight text-stone-900 dark:text-stone-100 font-sans">
              Your workspace
            </h1>
            <p class="text-sm font-normal text-stone-500 dark:text-stone-400 mt-1">
              Set a goal. Follow the work. Review the result.
            </p>
          </div>
          <div class="text-left sm:text-right shrink-0">
            <p class="text-sm font-semibold text-stone-800 dark:text-stone-200">
              {{ formattedDate }}
            </p>
            <p class="text-xs text-stone-400 dark:text-stone-500">
              Operations workspace
            </p>
          </div>
        </header>

        <!-- Goal Banner / Composer -->
        <div class="relative overflow-hidden rounded-3xl bg-stone-100/70 dark:bg-stone-900/80 border border-stone-200 dark:border-stone-800 p-6 md:p-8 shadow-xs">
          <!-- Decorative Background Asset -->
          <div
            class="absolute right-0 top-0 bottom-0 w-1/2 max-w-lg lg:max-w-xl xl:max-w-2xl pointer-events-none opacity-30 dark:opacity-15 hidden md:block overflow-hidden"
            aria-hidden="true"
          >
            <img
              src="/hero-banner.jpg"
              alt=""
              class="w-full h-full object-contain object-right mask-illustration"
            >
          </div>

          <div class="relative z-10 max-w-2xl">
            <span class="inline-block text-xs font-semibold tracking-normal text-emerald-600 dark:text-emerald-400 uppercase mb-1.5">
              Welcome to NagareOS
            </span>
            <h2 class="text-xl sm:text-2xl font-semibold text-stone-900 dark:text-stone-100 tracking-tight leading-snug mb-4 max-w-xl text-balance">
              Start with a goal and your workspace will begin to fill itself.
            </h2>

            <!-- Composer Input Card -->
            <div class="bg-white dark:bg-stone-900 rounded-2xl border border-stone-200 dark:border-stone-800 shadow-xs p-3.5 sm:p-4 transition-[border-color,box-shadow] duration-150 ease-out focus-within:ring-2 focus-within:ring-emerald-500/30 dark:focus-within:ring-emerald-400/30 focus-within:border-emerald-600 dark:focus-within:border-emerald-500">
              <label
                for="workspace-goal-input"
                class="sr-only"
              >Workspace goal or task description</label>
              <textarea
                id="workspace-goal-input"
                ref="goalTextarea"
                v-model="goalText"
                rows="2"
                placeholder="What would you like to accomplish?"
                aria-label="Workspace goal or task description"
                class="w-full resize-none bg-transparent outline-none text-stone-900 dark:text-stone-100 placeholder-stone-400 dark:placeholder-stone-500 text-sm sm:text-base leading-relaxed"
                :disabled="submittingGoal"
                @keydown="handleKeyDown"
              />

              <!-- Actions Bar -->
              <div class="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-stone-100 dark:border-stone-800">
                <div class="flex items-center gap-2">
                  <!-- Tools Dropdown -->
                  <div
                    ref="toolsDropdownRef"
                    class="relative"
                    @keydown.esc="showToolsDropdown = false"
                  >
                    <button
                      type="button"
                      aria-haspopup="menu"
                      :aria-expanded="showToolsDropdown"
                      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-stone-700 dark:text-stone-200 hover:text-stone-900 dark:hover:text-white hover:bg-stone-100 dark:hover:bg-stone-800 active:scale-95 motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[background-color,color,transform] duration-150 ease-out cursor-pointer"
                      :class="{ 'bg-stone-100 dark:bg-stone-800 text-stone-900 dark:text-white': showToolsDropdown }"
                      @click="showToolsDropdown = !showToolsDropdown"
                    >
                      <SlidersHorizontal
                        :size="14"
                        aria-hidden="true"
                      />
                      <span>Tools</span>
                      <ChevronDown
                        :size="13"
                        aria-hidden="true"
                        class="text-stone-500 dark:text-stone-400 transition-transform duration-150 ease-out motion-reduce:transition-none"
                        :class="{ 'rotate-180': showToolsDropdown }"
                      />
                    </button>

                    <!-- Tools Menu -->
                    <Transition
                      enter-active-class="transition-[opacity,transform] duration-150 ease-out origin-bottom-left motion-reduce:transition-none"
                      enter-from-class="opacity-0 scale-95"
                      enter-to-class="opacity-100 scale-100"
                      leave-active-class="transition-[opacity,transform] duration-100 ease-in origin-bottom-left motion-reduce:transition-none"
                      leave-from-class="opacity-100 scale-100"
                      leave-to-class="opacity-0 scale-95"
                    >
                      <div
                        v-if="showToolsDropdown"
                        role="menu"
                        aria-label="Configured tools"
                        class="absolute left-0 bottom-full mb-2 w-56 rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-lg p-2 z-50 text-xs motion-reduce:transition-none"
                      >
                        <div class="px-2 py-1 font-semibold text-stone-400 text-xs uppercase tracking-normal">
                          Configured tools
                        </div>
                        <div
                          v-if="mcpServers.length === 0"
                          class="px-2 py-2 text-stone-500 dark:text-stone-400"
                        >
                          No external tools linked.
                          <NuxtLink
                            to="/mcp"
                            class="text-emerald-600 dark:text-emerald-400 hover:underline block mt-1"
                          >
                            Configure MCP &rarr;
                          </NuxtLink>
                        </div>
                        <NuxtLink
                          v-for="server in mcpServers"
                          :key="server.name"
                          to="/mcp"
                          role="menuitem"
                          class="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-stone-100 dark:hover:bg-stone-800 text-left text-stone-700 dark:text-stone-300 transition-colors duration-100"
                          @click="showToolsDropdown = false"
                        >
                          <Cpu
                            :size="13"
                            aria-hidden="true"
                          />
                          <span class="truncate">{{ server.name }}</span>
                        </NuxtLink>
                      </div>
                    </Transition>
                  </div>

                  <!-- Mode Switcher -->
                  <fieldset class="hidden sm:flex items-center bg-stone-100 dark:bg-stone-800 rounded-lg p-0.5 text-xs font-medium">
                    <legend class="sr-only">
                      Composer mode
                    </legend>
                    <label
                      v-for="mode in (['agent', 'chat'] as const)"
                      :key="mode"
                      class="relative cursor-pointer"
                    >
                      <input
                        v-model="composerMode"
                        type="radio"
                        name="composer-mode"
                        :value="mode"
                        class="peer sr-only"
                      >
                      <span class="block px-2.5 py-1 rounded-md capitalize text-stone-600 dark:text-stone-400 peer-checked:bg-white dark:peer-checked:bg-stone-700 peer-checked:text-emerald-700 dark:peer-checked:text-emerald-400 peer-checked:shadow-xs peer-checked:font-semibold peer-focus-visible:ring-2 peer-focus-visible:ring-emerald-500">
                        {{ mode }}
                      </span>
                    </label>
                  </fieldset>
                </div>

                <div class="flex items-center gap-3">
                  <span class="text-xs text-stone-400 dark:text-stone-500 hidden md:inline">
                    Enter ↵ to run
                  </span>
                  <!-- Submit Button -->
                  <button
                    type="button"
                    class="flex items-center gap-2 px-5 py-2 rounded-full text-sm font-semibold transition-[background-color,transform] duration-150 ease-out shadow-xs cursor-pointer bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 active:scale-[0.98] motion-reduce:transform-none text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:bg-stone-200 dark:disabled:bg-stone-800 disabled:text-stone-400 dark:disabled:text-stone-500 disabled:shadow-none disabled:cursor-not-allowed disabled:active:scale-100"
                    :disabled="!goalText.trim() || submittingGoal"
                    @click="startFirstTask"
                  >
                    <Loader2
                      v-if="submittingGoal"
                      :size="15"
                      class="animate-spin"
                      aria-hidden="true"
                    />
                    <Play
                      v-else
                      :size="14"
                      class="fill-current"
                      aria-hidden="true"
                    />
                    <span>{{ allSessions.length === 0 ? 'Start first task' : 'Start task' }}</span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Quick Action Links -->
            <div class="flex flex-wrap items-center gap-3 mt-3.5">
              <NuxtLink
                to="/mcp"
                class="group inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white dark:bg-stone-900 hover:bg-stone-50 dark:hover:bg-stone-800 active:scale-[0.98] border border-stone-200 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700 text-xs font-medium text-stone-800 dark:text-stone-200 shadow-2xs transition-[background-color,border-color,transform] duration-150 ease-out motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              >
                <Plug
                  :size="13"
                  class="text-emerald-600 dark:text-emerald-400"
                  aria-hidden="true"
                />
                <span>Connect tools</span>
                <ChevronRight
                  :size="13"
                  class="text-stone-400 group-hover:text-stone-600 dark:group-hover:text-stone-200 transition-colors duration-150"
                  aria-hidden="true"
                />
              </NuxtLink>

              <NuxtLink
                to="/agents"
                class="group inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white dark:bg-stone-900 hover:bg-stone-50 dark:hover:bg-stone-800 active:scale-[0.98] border border-stone-200 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700 text-xs font-medium text-stone-800 dark:text-stone-200 shadow-2xs transition-[background-color,border-color,transform] duration-150 ease-out motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
              >
                <Bot
                  :size="13"
                  class="text-emerald-600 dark:text-emerald-400"
                  aria-hidden="true"
                />
                <span>Explore agents</span>
                <ChevronRight
                  :size="13"
                  class="text-stone-400 group-hover:text-stone-600 dark:group-hover:text-stone-200 transition-colors duration-150"
                  aria-hidden="true"
                />
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- Section 1: Active Work -->
        <section
          class="space-y-3"
          aria-labelledby="heading-active-work"
        >
          <div class="flex items-center justify-between">
            <h2
              id="heading-active-work"
              class="text-lg sm:text-xl font-semibold text-stone-900 dark:text-stone-100 tracking-tight"
            >
              Active work
            </h2>
            <button
              type="button"
              aria-label="View all active tasks"
              class="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 inline-flex items-center gap-1.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded-lg px-2.5 py-1 min-h-[32px] active:scale-95 motion-reduce:transform-none transition-[color,transform] duration-150 ease-out"
              @click="showSearchModal = true"
            >
              <span>View all</span>
              <ArrowRight
                :size="13"
                aria-hidden="true"
              />
            </button>
          </div>

          <!-- Empty State -->
          <div
            v-if="activeSessions.length === 0"
            class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center"
          >
            <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 flex items-center justify-center mb-3">
              <Folder
                :size="22"
                aria-hidden="true"
              />
            </div>
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100 mb-1">
              No active work yet
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm mb-4">
              Create your first task to start collaborating with agents.
            </p>
            <button
              type="button"
              class="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 active:scale-[0.98] motion-reduce:transform-none text-white text-xs font-semibold shadow-xs transition-[background-color,transform] duration-150 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 cursor-pointer"
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
              class="flex items-center justify-between p-4 hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors duration-150 ease-out group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-inset"
            >
              <div class="flex items-center gap-3.5 min-w-0 pr-4">
                <div class="w-9 h-9 rounded-xl bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 flex items-center justify-center shrink-0">
                  <Folder
                    :size="18"
                    aria-hidden="true"
                  />
                </div>
                <div class="min-w-0">
                  <h3 class="text-sm font-medium text-stone-900 dark:text-stone-100 truncate group-hover:text-emerald-600 transition-colors duration-150">
                    {{ s.name }}
                  </h3>
                  <p class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                    {{ s.last_message_content || 'Session initialized' }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-xs text-stone-400 dark:text-stone-500">
                  {{ formatRelativeTime(s.updated_at || s.created_at) }}
                </span>
                <ChevronRight
                  :size="15"
                  class="text-stone-400 group-hover:translate-x-0.5 transition-transform duration-150 ease-out motion-reduce:transform-none"
                  aria-hidden="true"
                />
              </div>
            </NuxtLink>
          </div>
        </section>

        <!-- Section 2: Needs Your Decision -->
        <section
          class="space-y-3"
          aria-labelledby="heading-decisions"
        >
          <div class="flex items-center justify-between">
            <h2
              id="heading-decisions"
              class="text-lg sm:text-xl font-semibold text-stone-900 dark:text-stone-100 tracking-tight"
            >
              Needs your decision
            </h2>
            <NuxtLink
              to="/logs"
              aria-label="View all decisions and logs"
              class="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 inline-flex items-center gap-1.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded-lg px-2.5 py-1 min-h-[32px] active:scale-95 motion-reduce:transform-none transition-[color,transform] duration-150 ease-out"
            >
              <span>View all</span>
              <ArrowRight
                :size="13"
                aria-hidden="true"
              />
            </NuxtLink>
          </div>

          <!-- Empty State -->
          <div class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center">
            <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 flex items-center justify-center mb-3">
              <CheckCircle2
                :size="22"
                aria-hidden="true"
              />
            </div>
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100 mb-1">
              No decisions pending
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm">
              When an agent pauses for confirmation or input, review it here.
            </p>
          </div>
        </section>

        <!-- Section 3: Recently Completed -->
        <section
          class="space-y-3"
          aria-labelledby="heading-completed"
        >
          <div class="flex items-center justify-between">
            <h2
              id="heading-completed"
              class="text-lg sm:text-xl font-semibold text-stone-900 dark:text-stone-100 tracking-tight"
            >
              Recently completed
            </h2>
            <button
              type="button"
              aria-label="View all completed tasks"
              class="text-xs font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 inline-flex items-center gap-1.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 rounded-lg px-2.5 py-1 min-h-[32px] active:scale-95 motion-reduce:transform-none transition-[color,transform] duration-150 ease-out"
              @click="showSearchModal = true"
            >
              <span>View all</span>
              <ArrowRight
                :size="13"
                aria-hidden="true"
              />
            </button>
          </div>

          <!-- Empty State -->
          <div
            v-if="completedSessions.length === 0"
            class="rounded-2xl border border-stone-200/80 dark:border-stone-800 bg-white dark:bg-stone-900 p-8 flex flex-col items-center justify-center text-center"
          >
            <div class="w-12 h-12 rounded-full bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 flex items-center justify-center mb-3">
              <Trophy
                :size="22"
                aria-hidden="true"
              />
            </div>
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100 mb-1">
              No completed tasks
            </h3>
            <p class="text-xs text-stone-500 dark:text-stone-400 max-w-sm">
              Completed sessions will appear here once tasks finish.
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
              class="flex items-center justify-between p-4 hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors duration-150 ease-out group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-inset"
            >
              <div class="flex items-center gap-3.5 min-w-0 pr-4">
                <div class="w-9 h-9 rounded-xl bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 flex items-center justify-center shrink-0">
                  <Trophy
                    :size="18"
                    aria-hidden="true"
                  />
                </div>
                <div class="min-w-0">
                  <h3 class="text-sm font-medium text-stone-900 dark:text-stone-100 truncate group-hover:text-emerald-600 transition-colors duration-150">
                    {{ s.name }}
                  </h3>
                  <p class="text-xs text-stone-500 dark:text-stone-400 truncate mt-0.5">
                    {{ s.last_message_content || 'Completed task' }}
                  </p>
                </div>
              </div>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-xs text-stone-400 dark:text-stone-500">
                  {{ formatRelativeTime(s.updated_at || s.created_at) }}
                </span>
                <ChevronRight
                  :size="15"
                  class="text-stone-400 group-hover:translate-x-0.5 transition-transform duration-150 ease-out motion-reduce:transform-none"
                  aria-hidden="true"
                />
              </div>
            </NuxtLink>
          </div>
        </section>
      </div>

      <!-- Right Column: Search, Getting Started, Stats & Tips -->
      <aside
        class="w-full lg:w-80 xl:w-88 shrink-0 space-y-6"
        aria-label="Workspace sidebar"
      >
        <!-- Top Search Bar & Notification -->
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex-1 flex items-center justify-between px-3.5 py-2 rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-2xs cursor-pointer hover:border-stone-300 dark:hover:border-stone-700 active:scale-[0.99] motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[border-color,transform] duration-150 ease-out text-left"
            aria-label="Search workspace"
            @click="showSearchModal = true"
          >
            <div class="flex items-center gap-2 text-stone-400 text-xs">
              <Search
                :size="15"
                aria-hidden="true"
              />
              <span>Search workspace...</span>
            </div>
            <kbd class="px-1.5 py-0.5 text-xs font-mono bg-stone-100 dark:bg-stone-800 text-stone-500 dark:text-stone-400 rounded border border-stone-200 dark:border-stone-700">
              ⌘K
            </kbd>
          </button>

          <NuxtLink
            to="/logs"
            class="relative p-2.5 rounded-xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:border-stone-300 dark:hover:border-stone-700 active:scale-95 motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 shadow-2xs transition-[color,border-color,transform] duration-150 ease-out cursor-pointer"
            aria-label="Notifications (1 unread)"
          >
            <Bell
              :size="17"
              aria-hidden="true"
            />
            <span class="absolute top-2 right-2 w-2 h-2 rounded-full bg-emerald-600 dark:bg-emerald-500 ring-2 ring-white dark:ring-stone-900" />
          </NuxtLink>
        </div>

        <!-- Getting Started Progress Card -->
        <div class="rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-5 shadow-xs space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
              Getting started
            </h2>
            <span class="text-xs font-mono font-medium text-stone-500 dark:text-stone-400">
              {{ completedStepsCount }}/4 complete
            </span>
          </div>

          <!-- Steps Stepper -->
          <div class="space-y-3">
            <!-- Item 1 -->
            <NuxtLink
              to="/mcp"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 active:scale-[0.99] motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[background-color,transform] duration-150 ease-out group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors duration-150"
                  :class="step1Complete ? 'bg-emerald-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  <CheckCircle2
                    v-if="step1Complete"
                    :size="14"
                    aria-hidden="true"
                  />
                  <span v-else>1</span>
                  <span class="sr-only">({{ step1Complete ? 'Completed' : 'To do' }})</span>
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-medium text-stone-900 dark:text-stone-100 group-hover:text-emerald-600 transition-colors duration-150 truncate">
                    Connect your tools
                  </p>
                  <p class="text-xs text-stone-400 truncate">
                    Link your favorite apps
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-emerald-600 shrink-0 transition-colors duration-150"
                aria-hidden="true"
              />
            </NuxtLink>

            <!-- Item 2 -->
            <button
              type="button"
              class="w-full flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 active:scale-[0.99] motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[background-color,transform] duration-150 ease-out text-left group cursor-pointer"
              @click="focusGoalInput"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors duration-150"
                  :class="step2Complete ? 'bg-emerald-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  <CheckCircle2
                    v-if="step2Complete"
                    :size="14"
                    aria-hidden="true"
                  />
                  <span v-else>2</span>
                  <span class="sr-only">({{ step2Complete ? 'Completed' : 'To do' }})</span>
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-medium text-stone-900 dark:text-stone-100 group-hover:text-emerald-600 transition-colors duration-150 truncate">
                    Create your first task
                  </p>
                  <p class="text-xs text-stone-400 truncate">
                    Turn an idea into action
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-emerald-600 shrink-0 transition-colors duration-150"
                aria-hidden="true"
              />
            </button>

            <!-- Item 3 -->
            <NuxtLink
              to="/agents"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 active:scale-[0.99] motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[background-color,transform] duration-150 ease-out group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors duration-150"
                  :class="step3Complete ? 'bg-emerald-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  <CheckCircle2
                    v-if="step3Complete"
                    :size="14"
                    aria-hidden="true"
                  />
                  <span v-else>3</span>
                  <span class="sr-only">({{ step3Complete ? 'Completed' : 'To do' }})</span>
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-medium text-stone-900 dark:text-stone-100 group-hover:text-emerald-600 transition-colors duration-150 truncate">
                    Assign an agent
                  </p>
                  <p class="text-xs text-stone-400 truncate">
                    Let AI do the work for you
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-emerald-600 shrink-0 transition-colors duration-150"
                aria-hidden="true"
              />
            </NuxtLink>

            <!-- Item 4 -->
            <NuxtLink
              to="/evaluations"
              class="flex items-center justify-between p-2 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/50 active:scale-[0.99] motion-reduce:transform-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-[background-color,transform] duration-150 ease-out group"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors duration-150"
                  :class="step4Complete ? 'bg-emerald-600 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
                >
                  <CheckCircle2
                    v-if="step4Complete"
                    :size="14"
                    aria-hidden="true"
                  />
                  <span v-else>4</span>
                  <span class="sr-only">({{ step4Complete ? 'Completed' : 'To do' }})</span>
                </div>
                <div class="min-w-0">
                  <p class="text-xs font-medium text-stone-900 dark:text-stone-100 group-hover:text-emerald-600 transition-colors duration-150 truncate">
                    Review your first result
                  </p>
                  <p class="text-xs text-stone-400 truncate">
                    See what your agents deliver
                  </p>
                </div>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:text-emerald-600 shrink-0 transition-colors duration-150"
                aria-hidden="true"
              />
            </NuxtLink>
          </div>
        </div>

        <!-- 2x2 Metric Stat Cards -->
        <div class="grid grid-cols-2 gap-3">
          <!-- Active tasks -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-semibold text-stone-900 dark:text-stone-100 font-mono">
                {{ activeSessions.length }}
              </span>
              <Folder
                :size="18"
                class="text-stone-400"
                aria-hidden="true"
              />
            </div>
            <p class="text-xs font-medium text-stone-500 dark:text-stone-400 mt-2">
              Active tasks
            </p>
          </div>

          <!-- Results -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-semibold text-stone-900 dark:text-stone-100 font-mono">
                {{ evaluations.length }}
              </span>
              <BarChart2
                :size="18"
                class="text-stone-400"
                aria-hidden="true"
              />
            </div>
            <p class="text-xs font-medium text-stone-500 dark:text-stone-400 mt-2">
              Results
            </p>
          </div>

          <!-- Decisions pending -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-semibold text-stone-900 dark:text-stone-100 font-mono">
                0
              </span>
              <CheckCircle2
                :size="18"
                class="text-stone-400 dark:text-stone-500"
                aria-hidden="true"
              />
            </div>
            <p class="text-xs font-medium text-stone-500 dark:text-stone-400 mt-2">
              Decisions pending
            </p>
          </div>

          <!-- Avg. latency -->
          <div class="p-4 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-2xs">
            <div class="flex items-center justify-between">
              <span class="text-2xl font-semibold text-stone-900 dark:text-stone-100 font-mono">
                {{ avgLatency }}
              </span>
              <Cpu
                :size="18"
                class="text-emerald-500"
                aria-hidden="true"
              />
            </div>
            <p class="text-xs font-medium text-stone-500 dark:text-stone-400 mt-2">
              Avg. latency
            </p>
          </div>
        </div>

        <!-- Tips Card -->
        <div class="rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 p-5 shadow-xs space-y-4">
          <div class="flex items-center gap-2 text-stone-900 dark:text-stone-100">
            <Lightbulb
              :size="16"
              class="text-amber-500"
              aria-hidden="true"
            />
            <h2 class="text-sm font-semibold">
              Tips
            </h2>
          </div>

          <div class="space-y-3.5">
            <!-- Tip 1 -->
            <div class="flex items-start gap-3 text-xs">
              <Plug
                :size="15"
                class="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5"
                aria-hidden="true"
              />
              <div>
                <h3 class="font-medium text-stone-800 dark:text-stone-200">
                  Connect Slack, Notion, or Drive
                </h3>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  Give your agents the context they need.
                </p>
              </div>
            </div>

            <!-- Tip 2 -->
            <div class="flex items-start gap-3 text-xs">
              <MessageSquare
                :size="15"
                class="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5"
                aria-hidden="true"
              />
              <div>
                <h3 class="font-medium text-stone-800 dark:text-stone-200">
                  Describe your goal in plain language
                </h3>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  You don't need to be specific or technical.
                </p>
              </div>
            </div>

            <!-- Tip 3 -->
            <div class="flex items-start gap-3 text-xs">
              <Sparkles
                :size="15"
                class="text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5"
                aria-hidden="true"
              />
              <div>
                <h3 class="font-medium text-stone-800 dark:text-stone-200">
                  Agents organize work automatically
                </h3>
                <p class="text-stone-500 dark:text-stone-400 mt-0.5 leading-relaxed">
                  They break it down, take action, and keep you updated.
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- Search Modal / Global Command Palette -->
    <UModal v-model:open="showSearchModal">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <h2 class="text-base font-semibold text-stone-900 dark:text-stone-100">
            Search workspace
          </h2>
          <button
            type="button"
            aria-label="Close search"
            class="p-1.5 rounded-lg text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
            @click="showSearchModal = false"
          >
            <X
              :size="16"
              aria-hidden="true"
            />
          </button>
        </div>
      </template>

      <template #body>
        <div class="space-y-4">
          <div class="relative">
            <span
              class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-stone-400"
              aria-hidden="true"
            >
              <Search :size="16" />
            </span>
            <input
              v-model="searchQuery"
              type="text"
              aria-label="Search tasks, sessions or knowledge"
              class="w-full pl-10 pr-4 py-2.5 border border-stone-200 dark:border-stone-800 rounded-xl bg-stone-50 dark:bg-stone-900/50 text-sm outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-stone-800 dark:text-stone-200"
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
              class="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-800/40 transition-colors duration-150 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-inset"
              @click="showSearchModal = false"
            >
              <div class="min-w-0 pr-3">
                <p class="text-sm font-medium text-stone-800 dark:text-stone-200 truncate group-hover:text-emerald-600 transition-colors duration-150">
                  {{ s.name }}
                </p>
                <p class="text-xs text-stone-400 truncate mt-0.5">
                  {{ s.last_message_content || 'Session' }}
                </p>
              </div>
              <ChevronRight
                :size="14"
                class="text-stone-400 group-hover:translate-x-0.5 transition-transform duration-150 ease-out motion-reduce:transform-none shrink-0"
                aria-hidden="true"
              />
            </NuxtLink>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<style scoped>
.mask-illustration {
  mask-image: radial-gradient(ellipse 90% 85% at 75% 50%, black 40%, transparent 95%);
  -webkit-mask-image: radial-gradient(ellipse 90% 85% at 75% 50%, black 40%, transparent 95%);
}
</style>
