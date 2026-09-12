<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Check,
  AlertTriangle,
  Calendar,
  ChevronRight,
  ChevronDown,
  MoreHorizontal,
  MessageSquare,
  Bot,
  FileText,
  CheckSquare,
  Zap,
  ArrowRight,
  RefreshCw,
  ExternalLink,
  UserCheck,
  Plus,
  SlidersHorizontal,
  Info,
  X,
  AlertCircle
} from '@lucide/vue'
import { useApiInbox, type DecisionItem, type InboxStats } from '~/composables/useApi/inbox'

const api = useApiInbox()

const items = ref<DecisionItem[]>([])
const stats = ref<InboxStats | null>(null)
const selectedItemId = ref<string | null>(null)
const activeFilter = ref<'all' | 'urgent' | 'today' | 'this_week' | 'approved' | 'sent_back'>('all')
const loading = ref(true)
const actionLoading = ref(false)
const errorMessage = ref<string | null>(null)
const showCreateModal = ref(false)
const createSubmitting = ref(false)

const newDecision = ref({
  title: '',
  subtitle: '',
  priority: 'high',
  agent_name: 'Nova',
  agent_role: 'Marketing agent',
  project: 'Q2 launch campaign',
  summary: '',
  key_rationale_text: '',
  potential_risks_text: '',
  confidence_score: 92
})

const selectedItem = computed(() => {
  if (!items.value.length) return null
  return items.value.find(i => i.id === selectedItemId.value) || items.value[0]
})

const loadData = async (silent = false) => {
  if (!silent) loading.value = true
  errorMessage.value = null
  try {
    const [fetchedItems, fetchedStats] = await Promise.all([
      api.list(activeFilter.value),
      api.stats()
    ])
    items.value = fetchedItems
    stats.value = fetchedStats
    if (items.value.length && (!selectedItemId.value || !items.value.some(i => i.id === selectedItemId.value))) {
      selectedItemId.value = items.value[0]?.id ?? null
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Failed to fetch inbox data'
    errorMessage.value = message
  } finally {
    if (!silent) loading.value = false
  }
}

let pollInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  void loadData()
  pollInterval = setInterval(() => {
    void loadData(true)
  }, 30000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const handleFilterChange = async (filter: typeof activeFilter.value) => {
  activeFilter.value = filter
  await loadData()
}

const handleSelectAlternative = async (altId: string) => {
  if (!selectedItem.value) return
  selectedItem.value.selected_alternative = altId
  try {
    await api.patch(selectedItem.value.id, { selected_alternative: altId })
  } catch (err: unknown) {
    console.error('Failed to update alternative:', err)
  }
}

const handleApprove = async () => {
  if (!selectedItem.value || actionLoading.value) return
  actionLoading.value = true
  errorMessage.value = null
  try {
    await api.approve(selectedItem.value.id)
    await loadData()
  } catch (err: unknown) {
    errorMessage.value = err instanceof Error ? err.message : 'Failed to approve decision'
  } finally {
    actionLoading.value = false
  }
}

const handleRequestChanges = async () => {
  if (!selectedItem.value || actionLoading.value) return
  actionLoading.value = true
  errorMessage.value = null
  try {
    await api.requestChanges(selectedItem.value.id)
    await loadData()
  } catch (err: unknown) {
    errorMessage.value = err instanceof Error ? err.message : 'Failed to request changes'
  } finally {
    actionLoading.value = false
  }
}

const handleAssignBack = async () => {
  if (!selectedItem.value || actionLoading.value) return
  actionLoading.value = true
  errorMessage.value = null
  try {
    await api.assignBack(selectedItem.value.id)
    await loadData()
  } catch (err: unknown) {
    errorMessage.value = err instanceof Error ? err.message : 'Failed to assign back'
  } finally {
    actionLoading.value = false
  }
}

const handleCreateDecision = async () => {
  if (!newDecision.value.title.trim() || createSubmitting.value) return
  createSubmitting.value = true
  errorMessage.value = null
  try {
    const rationaleList = newDecision.value.key_rationale_text
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)
    const risksList = newDecision.value.potential_risks_text
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean)

    await api.create({
      title: newDecision.value.title.trim(),
      subtitle: newDecision.value.subtitle.trim(),
      priority: newDecision.value.priority,
      priority_label: newDecision.value.priority === 'urgent' ? 'Urgent' : newDecision.value.priority === 'high' ? 'High priority' : newDecision.value.priority === 'medium' ? 'Medium risk' : 'Normal',
      agent_name: newDecision.value.agent_name.trim(),
      agent_role: newDecision.value.agent_role.trim(),
      project: newDecision.value.project.trim(),
      summary: newDecision.value.summary.trim(),
      key_rationale: rationaleList,
      potential_risks: risksList,
      confidence_score: Number(newDecision.value.confidence_score) || 90,
      alternatives: [
        {
          id: 'opt-a',
          label: 'Option A (Recommended)',
          name: 'Primary direction',
          description: 'Optimized proposal based on initial analysis.',
          recommended: true
        }
      ]
    })

    showCreateModal.value = false
    newDecision.value = {
      title: '',
      subtitle: '',
      priority: 'high',
      agent_name: 'Nova',
      agent_role: 'Marketing agent',
      project: 'Q2 launch campaign',
      summary: '',
      key_rationale_text: '',
      potential_risks_text: '',
      confidence_score: 92
    }
    await loadData()
  } catch (err: unknown) {
    errorMessage.value = err instanceof Error ? err.message : 'Failed to create decision'
  } finally {
    createSubmitting.value = false
  }
}

const getPriorityColor = (priority: string) => {
  const p = (priority || '').toLowerCase()
  switch (p) {
    case 'urgent':
    case 'high':
      return {
        bg: 'bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 border-red-200 dark:border-red-900/40',
        dot: 'bg-red-500',
        label: p === 'urgent' ? 'Urgent' : 'High priority'
      }
    case 'medium':
      return {
        bg: 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900/40',
        dot: 'bg-amber-500',
        label: 'Medium risk'
      }
    case 'low':
      return {
        bg: 'bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-900/40',
        dot: 'bg-blue-500',
        label: 'Low risk'
      }
    default:
      return {
        bg: 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-300 border-stone-200 dark:border-stone-700',
        dot: 'bg-stone-400',
        label: 'Normal'
      }
  }
}

const getAgentBg = (role: string) => {
  const r = (role || '').toLowerCase()
  if (r.includes('marketing') || r.includes('design')) return 'bg-purple-600 text-white'
  if (r.includes('research')) return 'bg-stone-800 text-white dark:bg-stone-700'
  if (r.includes('data')) return 'bg-emerald-600 text-white'
  return 'bg-blue-600 text-white'
}
</script>

<template>
  <div class="flex-1 flex flex-col min-h-0 bg-stone-50/60 dark:bg-stone-950 text-stone-900 dark:text-stone-100 overflow-y-auto">
    <!-- Error Notification Banner -->
    <div
      v-if="errorMessage"
      class="px-6 py-2.5 bg-red-50 dark:bg-red-950/40 border-b border-red-200 dark:border-red-900/40 flex items-center justify-between text-xs text-red-700 dark:text-red-300 shrink-0"
    >
      <div class="flex items-center gap-2">
        <AlertCircle :size="14" />
        <span>{{ errorMessage }}</span>
      </div>
      <button
        class="text-red-500 hover:text-red-700 dark:hover:text-red-300"
        @click="errorMessage = null"
      >
        <X :size="14" />
      </button>
    </div>

    <!-- MAIN CONTAINER -->
    <div class="flex-1 max-w-[1720px] w-full mx-auto p-4 md:p-6 lg:p-8 flex flex-col">
      <!-- HEADER (EMPTY STATE VERSION) -->
      <div
        v-if="!loading && items.length === 0"
        class="mb-6"
      >
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
              Inbox
            </h1>
            <p class="mt-1 text-sm text-stone-500 dark:text-stone-400">
              All updates from your agents, tasks, and systems.
            </p>
          </div>
          <div class="flex items-center gap-2 self-start md:self-auto">
            <button
              class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1 shadow-sm transition"
              @click="showCreateModal = true"
            >
              <Plus :size="14" /> New decision
            </button>
            <button class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-200 dark:border-stone-800 text-xs font-medium text-stone-600 dark:text-stone-300 bg-white dark:bg-stone-900 shadow-sm">
              Newest <ChevronDown :size="14" />
            </button>
            <button class="p-1.5 rounded-lg border border-stone-200 dark:border-stone-800 text-stone-500 bg-white dark:bg-stone-900 shadow-sm">
              <MoreHorizontal :size="16" />
            </button>
          </div>
        </div>

        <!-- Filter tabs for empty state -->
        <div class="mt-6 flex flex-wrap items-center gap-2 border-b border-transparent pb-1">
          <button class="px-4 py-1.5 rounded-full text-xs font-semibold bg-blue-600 text-white shadow-sm">
            All
          </button>
          <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60 transition">
            <span>@</span> Mentions
          </button>
          <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60 transition">
            <Calendar :size="13" /> Task updates
          </button>
          <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60 transition">
            <MessageSquare :size="13" /> Agent messages
          </button>
          <button class="flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60 transition">
            <SlidersHorizontal :size="13" /> System
          </button>
        </div>
      </div>

      <!-- HEADER (DATA STATE VERSION) -->
      <div
        v-else-if="!loading"
        class="mb-6"
      >
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
              Decision inbox
            </h1>
            <p class="mt-1 text-sm text-stone-500 dark:text-stone-400">
              Only the moments that need your judgment.
            </p>
          </div>
          <div class="flex items-center gap-4 self-start md:self-auto">
            <button
              class="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
              @click="showCreateModal = true"
            >
              <Plus :size="14" /> New decision
            </button>
            <div class="text-right">
              <p class="text-sm font-semibold text-stone-800 dark:text-stone-200">
                Mon, Apr 28, 2025
              </p>
              <p class="text-xs text-stone-400">
                A calmer, more productive day.
              </p>
            </div>
          </div>
        </div>

        <!-- Filter tabs for data state -->
        <div class="mt-6 flex flex-wrap items-center gap-2 border-b border-transparent pb-1">
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold transition"
            :class="activeFilter === 'all' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('all')"
          >
            <span>All</span>
            <span
              class="px-1.5 py-0.2 rounded-full text-[10px]"
              :class="activeFilter === 'all' ? 'bg-blue-700 text-white' : 'bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400'"
            >{{ stats?.total_pending ?? items.length }}</span>
          </button>
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition"
            :class="activeFilter === 'urgent' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('urgent')"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-red-500" />
            <span>Urgent</span>
            <span class="text-[10px] text-stone-400">{{ stats?.urgent_count ?? 0 }}</span>
          </button>
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition"
            :class="activeFilter === 'today' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('today')"
          >
            <Calendar :size="13" />
            <span>Today</span>
            <span class="text-[10px] text-stone-400">{{ stats?.today_count ?? 0 }}</span>
          </button>
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition"
            :class="activeFilter === 'this_week' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('this_week')"
          >
            <Calendar :size="13" />
            <span>This week</span>
            <span class="text-[10px] text-stone-400">{{ stats?.this_week_count ?? 0 }}</span>
          </button>
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition"
            :class="activeFilter === 'approved' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('approved')"
          >
            <Check
              :size="13"
              class="text-emerald-500"
            />
            <span>Approved</span>
            <span class="text-[10px] text-stone-400">{{ stats?.approved_count ?? 0 }}</span>
          </button>
          <button
            class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition"
            :class="activeFilter === 'sent_back' ? 'bg-blue-600 text-white shadow-sm' : 'bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/60'"
            @click="handleFilterChange('sent_back')"
          >
            <RefreshCw :size="13" />
            <span>Sent back</span>
            <span class="text-[10px] text-stone-400">{{ stats?.sent_back_count ?? 0 }}</span>
          </button>
        </div>
      </div>

      <!-- LOADING SKELETON -->
      <div
        v-if="loading"
        class="flex-1 flex flex-col items-center justify-center py-20 text-stone-400"
      >
        <RefreshCw
          :size="28"
          class="animate-spin mb-3 text-blue-600"
        />
        <p class="text-sm">
          Loading inbox...
        </p>
      </div>

      <!-- EMPTY STATE VIEW -->
      <div
        v-else-if="items.length === 0"
        class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6"
      >
        <!-- Main Empty Card -->
        <div class="lg:col-span-8 xl:col-span-9 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-10 flex flex-col items-center justify-center text-center min-h-[500px] shadow-sm">
          <!-- Custom Tray Graphic with radiating icon badges -->
          <div class="relative w-56 h-44 mb-6 flex items-center justify-center">
            <!-- Arcs / Dashed lines -->
            <svg
              class="absolute inset-0 w-full h-full text-stone-300 dark:text-stone-700 pointer-events-none"
              viewBox="0 0 220 170"
              fill="none"
            >
              <path
                d="M 40 50 Q 80 90 110 100"
                stroke="currentColor"
                stroke-dasharray="3 3"
                stroke-width="1.5"
              />
              <path
                d="M 100 30 Q 105 70 110 100"
                stroke="currentColor"
                stroke-dasharray="3 3"
                stroke-width="1.5"
              />
              <path
                d="M 170 45 Q 135 80 110 100"
                stroke="currentColor"
                stroke-dasharray="3 3"
                stroke-width="1.5"
              />
              <path
                d="M 190 90 Q 150 100 110 100"
                stroke="currentColor"
                stroke-dasharray="3 3"
                stroke-width="1.5"
              />
            </svg>

            <!-- 4 Orbit Badges -->
            <div class="absolute top-4 left-6 w-9 h-9 rounded-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center shadow-sm text-stone-500">
              <MessageSquare :size="16" />
            </div>
            <div class="absolute top-0 left-24 w-9 h-9 rounded-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center shadow-sm text-stone-500">
              <CheckSquare :size="16" />
            </div>
            <div class="absolute top-3 right-8 w-9 h-9 rounded-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center shadow-sm text-stone-500">
              <Bot :size="16" />
            </div>
            <div class="absolute top-16 right-2 w-9 h-9 rounded-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 flex items-center justify-center shadow-sm text-stone-500">
              <FileText :size="16" />
            </div>

            <!-- Central Inbox Tray -->
            <div class="relative z-10 w-28 h-18 mt-14">
              <svg
                viewBox="0 0 100 60"
                class="w-full h-full text-blue-500 fill-blue-50/60 dark:fill-blue-950/40"
              >
                <path
                  d="M 10 20 L 32 20 L 38 32 L 62 32 L 68 20 L 90 20 L 96 50 L 4 50 Z"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linejoin="round"
                />
                <path
                  d="M 2 50 C 2 54, 8 58, 14 58 L 86 58 C 92 58, 98 54, 98 50"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  fill="none"
                />
              </svg>
            </div>
          </div>

          <h2 class="text-xl font-bold text-stone-900 dark:text-stone-100">
            Your inbox is empty
          </h2>
          <p class="mt-2 text-sm text-stone-500 dark:text-stone-400 max-w-md">
            Updates from your agents, tasks, and systems will appear here as you start working.
          </p>

          <div class="mt-7 flex flex-col items-center gap-3">
            <button
              class="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm shadow-sm transition"
              @click="showCreateModal = true"
            >
              Create a task
            </button>
            <NuxtLink
              to="/agents"
              class="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 transition"
            >
              Explore agents <ArrowRight :size="14" />
            </NuxtLink>
          </div>
        </div>

        <!-- Right Sidebar (Empty state) -->
        <div class="lg:col-span-4 xl:col-span-3 space-y-6">
          <!-- Inbox Insights Card -->
          <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                Inbox insights
              </h3>
              <span class="text-xs text-stone-400 flex items-center gap-1 cursor-pointer">
                Last 7 days <ChevronDown :size="13" />
              </span>
            </div>
            <div class="py-10 flex flex-col items-center justify-center text-center">
              <div class="flex items-end gap-1.5 h-10 mb-3 opacity-30">
                <div class="w-1.5 h-6 bg-stone-500 rounded-full" />
                <div class="w-1.5 h-10 bg-stone-500 rounded-full" />
                <div class="w-1.5 h-7 bg-stone-500 rounded-full" />
              </div>
              <p class="text-sm font-semibold text-stone-800 dark:text-stone-200">
                No activity yet
              </p>
              <p class="mt-1 text-xs text-stone-400 max-w-xs">
                Insights will appear here once you have some activity.
              </p>
            </div>
          </div>

          <!-- Pending Approvals Card -->
          <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                Pending approvals
              </h3>
              <ChevronRight
                :size="15"
                class="text-stone-400"
              />
            </div>
            <div class="py-8 flex flex-col items-center justify-center text-center">
              <div class="w-10 h-10 rounded-xl bg-stone-100 dark:bg-stone-800 text-stone-400 flex items-center justify-center mb-3">
                <FileText :size="20" />
              </div>
              <p class="text-sm font-semibold text-stone-800 dark:text-stone-200">
                No pending approvals
              </p>
              <p class="mt-1 text-xs text-stone-400 max-w-xs">
                Items that need your decision will appear here.
              </p>
            </div>
          </div>

          <!-- Stay in control banner -->
          <div class="bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40 rounded-2xl p-5">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
                <Zap :size="16" />
              </div>
              <div>
                <h4 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                  Stay in control
                </h4>
                <p class="mt-1 text-xs text-stone-500 dark:text-stone-400 leading-relaxed">
                  Get notified about important updates will appear here.
                </p>
                <button class="mt-3.5 w-full py-2 rounded-lg bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 text-xs font-semibold text-stone-800 dark:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800 shadow-sm transition">
                  Manage notifications
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- DATA STATE VIEW (3-COLUMN SPLIT) -->
      <div
        v-else
        class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start"
      >
        <!-- COLUMN 1: Decision list (approx 3.5 cols) -->
        <div class="lg:col-span-4 xl:col-span-3.5 space-y-3">
          <div
            v-for="item in items"
            :key="item.id"
            class="p-4 rounded-2xl border bg-white dark:bg-stone-900 cursor-pointer transition shadow-sm relative"
            :class="selectedItem?.id === item.id ? 'border-blue-500 ring-2 ring-blue-500/20 dark:ring-blue-500/30' : 'border-stone-200 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700'"
            @click="selectedItemId = item.id"
          >
            <!-- Badge & Time -->
            <div class="flex items-center justify-between text-xs mb-2">
              <span
                class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-medium border"
                :class="getPriorityColor(item.priority).bg"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full"
                  :class="getPriorityColor(item.priority).dot"
                />
                {{ getPriorityColor(item.priority).label }}
              </span>
              <span class="text-stone-400 text-[11px]">{{ item.time_ago }}</span>
            </div>

            <!-- Title & Subtitle -->
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="font-bold text-sm text-stone-900 dark:text-stone-100 leading-snug">
                  {{ item.title }}
                </h3>
                <p class="mt-1 text-xs text-stone-500 dark:text-stone-400 line-clamp-2">
                  {{ item.subtitle }}
                </p>
              </div>
              <ChevronRight
                :size="15"
                class="text-stone-400 shrink-0 mt-0.5"
              />
            </div>

            <!-- Meta: Agent avatar, name, comments -->
            <div class="mt-3.5 pt-3 border-t border-stone-100 dark:border-stone-800/80 flex items-center justify-between text-xs text-stone-500">
              <div class="flex items-center gap-2">
                <div
                  class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                  :class="getAgentBg(item.agent_role)"
                >
                  {{ (item.agent_name || 'A')[0] }}
                </div>
                <span class="font-medium text-stone-700 dark:text-stone-300">{{ item.agent_name }}</span>
                <span class="text-stone-400 text-[11px]">{{ item.agent_role }}</span>
              </div>
              <div class="flex items-center gap-1 text-[11px] text-stone-400">
                <MessageSquare :size="12" />
                <span>{{ item.comments_count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- COLUMN 2: Selected Decision Detail Pane (approx 5.5 cols) -->
        <div
          v-if="selectedItem"
          class="lg:col-span-5 xl:col-span-5.5 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-6 lg:p-7 shadow-sm space-y-6"
        >
          <!-- Top Tag & Time -->
          <div class="flex items-center justify-between text-xs">
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-medium border"
              :class="getPriorityColor(selectedItem.priority).bg"
            >
              <span
                class="w-1.5 h-1.5 rounded-full"
                :class="getPriorityColor(selectedItem.priority).dot"
              />
              {{ getPriorityColor(selectedItem.priority).label }}
            </span>
            <span class="text-stone-400 text-xs">{{ selectedItem.time_ago }}</span>
          </div>

          <!-- Main Title -->
          <div>
            <h2 class="text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
              {{ selectedItem.title }}
            </h2>
            <p class="mt-1 text-sm text-stone-500 dark:text-stone-400">
              {{ selectedItem.subtitle }}
            </p>
          </div>

          <!-- Agent + Project Pill -->
          <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-stone-100 dark:border-stone-800">
            <div class="flex items-center gap-2.5">
              <div
                class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                :class="getAgentBg(selectedItem.agent_role)"
              >
                {{ (selectedItem.agent_name || 'A')[0] }}
              </div>
              <div>
                <span class="text-sm font-semibold text-stone-800 dark:text-stone-200">{{ selectedItem.agent_name }}</span>
                <span class="block text-[11px] text-stone-400">{{ selectedItem.agent_role }}</span>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <span class="px-2.5 py-1 rounded-md bg-stone-100 dark:bg-stone-800 text-xs font-medium text-stone-600 dark:text-stone-300 flex items-center gap-1.5">
                <CheckSquare :size="12" /> {{ selectedItem.project || 'Active initiative' }}
              </span>
              <span class="px-2 py-1 rounded-md text-xs text-stone-400 flex items-center gap-1">
                <MessageSquare :size="13" /> {{ selectedItem.comments_count }}
              </span>
              <button class="p-1 rounded text-stone-400 hover:text-stone-600">
                <MoreHorizontal :size="16" />
              </button>
            </div>
          </div>

          <!-- Summary & Confidence Score -->
          <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div class="md:col-span-8">
              <h4 class="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-1.5">
                Summary
              </h4>
              <p class="text-sm text-stone-600 dark:text-stone-300 leading-relaxed">
                {{ selectedItem.summary || 'Awaiting agent synthesis.' }}
              </p>
            </div>
            <div class="md:col-span-4 p-3.5 rounded-xl bg-stone-50 dark:bg-stone-800/60 border border-stone-200/80 dark:border-stone-700/80">
              <div class="flex items-center justify-between text-xs text-stone-500 mb-1">
                <span>Confidence score</span>
                <Info
                  :size="13"
                  class="text-stone-400"
                />
              </div>
              <div class="flex items-baseline gap-2">
                <span class="text-2xl font-bold text-stone-900 dark:text-stone-100">{{ selectedItem.confidence_score }}%</span>
              </div>
              <div class="w-full h-1.5 bg-stone-200 dark:bg-stone-700 rounded-full mt-2 overflow-hidden">
                <div
                  class="h-full bg-emerald-500 rounded-full"
                  :style="{ width: `${selectedItem.confidence_score}%` }"
                />
              </div>
              <p class="mt-2 text-[10px] text-stone-400 leading-normal">
                High confidence based on data, previous performance, and team input.
              </p>
            </div>
          </div>

          <!-- Key Rationale vs Potential Risks (2 Columns) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Key Rationale -->
            <div class="p-4 rounded-xl bg-stone-50/70 dark:bg-stone-800/40 border border-stone-200/80 dark:border-stone-800">
              <h4 class="text-xs font-semibold text-stone-700 dark:text-stone-300 mb-3 flex items-center gap-1.5">
                Key rationale
              </h4>
              <ul
                v-if="selectedItem.key_rationale && selectedItem.key_rationale.length"
                class="space-y-2.5"
              >
                <li
                  v-for="(point, idx) in selectedItem.key_rationale"
                  :key="idx"
                  class="text-xs text-stone-600 dark:text-stone-300 flex items-start gap-2"
                >
                  <div class="w-4 h-4 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Check :size="11" />
                  </div>
                  <span>{{ point }}</span>
                </li>
              </ul>
              <p
                v-else
                class="text-xs text-stone-400 italic"
              >
                No rationale recorded.
              </p>
            </div>

            <!-- Potential Risks -->
            <div class="p-4 rounded-xl bg-stone-50/70 dark:bg-stone-800/40 border border-stone-200/80 dark:border-stone-800">
              <h4 class="text-xs font-semibold text-stone-700 dark:text-stone-300 mb-3 flex items-center gap-1.5">
                Potential risks
              </h4>
              <ul
                v-if="selectedItem.potential_risks && selectedItem.potential_risks.length"
                class="space-y-2.5"
              >
                <li
                  v-for="(risk, idx) in selectedItem.potential_risks"
                  :key="idx"
                  class="text-xs text-stone-600 dark:text-stone-300 flex items-start gap-2"
                >
                  <div class="w-4 h-4 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                    <AlertTriangle :size="11" />
                  </div>
                  <span>{{ risk }}</span>
                </li>
              </ul>
              <p
                v-else
                class="text-xs text-stone-400 italic"
              >
                No specific risks identified.
              </p>
            </div>
          </div>

          <!-- Alternatives Considered -->
          <div v-if="selectedItem.alternatives && selectedItem.alternatives.length > 0">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">
              Alternatives considered
            </h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div
                v-for="alt in selectedItem.alternatives"
                :key="alt.id"
                class="p-3.5 rounded-xl border cursor-pointer transition relative flex flex-col justify-between"
                :class="selectedItem.selected_alternative === alt.id ? 'border-blue-500 bg-blue-50/30 dark:bg-blue-950/20 ring-1 ring-blue-500/20' : 'border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 hover:border-stone-300'"
                @click="handleSelectAlternative(alt.id)"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <input
                      type="radio"
                      :checked="selectedItem.selected_alternative === alt.id"
                      class="text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                    >
                    <span class="text-xs font-bold text-stone-900 dark:text-stone-100">{{ alt.label }}</span>
                  </div>
                  <p class="mt-1 text-[11px] font-semibold text-stone-700 dark:text-stone-300">
                    {{ alt.name }}
                  </p>
                  <p
                    v-if="alt.description"
                    class="mt-1 text-[10px] text-stone-400 leading-snug"
                  >
                    {{ alt.description }}
                  </p>
                </div>
                <div class="mt-3 pt-2.5 border-t border-stone-100 dark:border-stone-800/80 grid grid-cols-2 gap-y-1.5 text-[10px]">
                  <span class="text-stone-400">Estimated reach</span>
                  <span class="font-medium text-right text-stone-700 dark:text-stone-300">{{ alt.estimated_reach || '-' }}</span>
                  <span class="text-stone-400">Estimated cost</span>
                  <span class="font-medium text-right text-stone-700 dark:text-stone-300">{{ alt.estimated_cost || '-' }}</span>
                  <span class="text-stone-400">Expected lift</span>
                  <span class="font-medium text-right text-emerald-600 dark:text-emerald-400">{{ alt.expected_lift || '-' }}</span>
                  <span class="text-stone-400">Timeline</span>
                  <span class="font-medium text-right text-stone-700 dark:text-stone-300">{{ alt.timeline || '-' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Supporting Materials -->
          <div v-if="selectedItem.files && selectedItem.files.length > 0">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
              Supporting materials
            </h4>
            <div class="flex flex-wrap items-center gap-2.5">
              <div
                v-for="(mat, idx) in selectedItem.files"
                :key="idx"
                class="flex items-center gap-2.5 px-3 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-stone-50/50 dark:bg-stone-850 hover:bg-stone-100 transition text-xs"
              >
                <div
                  class="w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold"
                  :class="mat.type === 'pdf' ? 'bg-red-100 text-red-600' : mat.type === 'xlsx' ? 'bg-emerald-100 text-emerald-600' : 'bg-blue-100 text-blue-600'"
                >
                  {{ mat.type.toUpperCase() }}
                </div>
                <div>
                  <span class="font-medium text-stone-800 dark:text-stone-200">{{ mat.name }}</span>
                  <span class="block text-[10px] text-stone-400">{{ mat.size }}</span>
                </div>
              </div>
              <button class="p-2 rounded-xl border border-stone-200 dark:border-stone-800 text-stone-400 hover:text-stone-600">
                <MoreHorizontal :size="16" />
              </button>
            </div>
          </div>

          <!-- Action Footer Bar -->
          <div class="pt-4 border-t border-stone-200 dark:border-stone-800 flex flex-wrap items-center gap-2.5">
            <button
              class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center gap-1.5 shadow-sm transition disabled:opacity-50"
              :disabled="actionLoading"
              @click="handleApprove"
            >
              <Check :size="14" /> Approve
            </button>
            <button
              class="px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-200 font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-50"
              :disabled="actionLoading"
              @click="handleRequestChanges"
            >
              <MessageSquare :size="14" /> Request changes
            </button>
            <button
              class="px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-200 font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-50"
              :disabled="actionLoading"
              @click="handleAssignBack"
            >
              <UserCheck :size="14" /> Assign back
            </button>
            <NuxtLink
              to="/tasks"
              class="px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-700 hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-200 font-semibold text-xs flex items-center gap-1.5 transition ml-auto"
            >
              <ExternalLink :size="14" /> Open task
            </NuxtLink>
          </div>
        </div>

        <!-- COLUMN 3: Right Sidebar (Insights, Approvals, Alerts) (~3 cols) -->
        <div class="lg:col-span-3 space-y-6">
          <!-- Inbox Insights with trends -->
          <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                Inbox insights
              </h3>
              <span class="text-xs text-stone-400 flex items-center gap-1 cursor-pointer">
                Last 7 days <ChevronDown :size="13" />
              </span>
            </div>

            <!-- Stats Metric 1: Avg time -->
            <div class="grid grid-cols-3 gap-2 text-center py-2">
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/50">
                <span class="text-lg font-bold text-stone-900 dark:text-stone-100">{{ stats?.avg_time ?? '2.8h' }}</span>
                <span class="block text-[10px] text-stone-400">Avg. time to approve</span>
                <span class="inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mt-1">
                  ↓ 32%
                </span>
              </div>

              <!-- Stats Metric 2: Pending decisions -->
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/50">
                <span class="text-lg font-bold text-stone-900 dark:text-stone-100">{{ stats?.pending_count ?? items.length }}</span>
                <span class="block text-[10px] text-stone-400">Pending decisions</span>
                <span class="inline-flex items-center gap-0.5 text-[10px] font-semibold text-red-500 mt-1">
                  ↑ 2
                </span>
              </div>

              <!-- Stats Metric 3: SLA risk -->
              <div class="p-2.5 rounded-xl bg-stone-50 dark:bg-stone-800/50">
                <span class="text-lg font-bold text-stone-900 dark:text-stone-100">{{ stats?.sla_risk_count ?? 0 }}</span>
                <span class="block text-[10px] text-stone-400">At SLA risk</span>
                <span class="inline-flex items-center gap-0.5 text-[10px] font-semibold text-red-500 mt-1">
                  ↓ 1
                </span>
              </div>
            </div>
          </div>

          <!-- My Pending Approvals List -->
          <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-5 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                My pending approvals
              </h3>
              <NuxtLink
                to="/inbox"
                class="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                View all <ArrowRight :size="12" />
              </NuxtLink>
            </div>

            <div
              v-if="items.length > 0"
              class="divide-y divide-stone-100 dark:divide-stone-800"
            >
              <div
                v-for="item in items.slice(0, 6)"
                :key="item.id"
                class="py-2.5 flex items-center justify-between cursor-pointer hover:bg-stone-50 dark:hover:bg-stone-800/40 rounded-lg px-2 -mx-2 transition"
                @click="selectedItemId = item.id"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span
                    class="w-2 h-2 rounded-full shrink-0"
                    :class="getPriorityColor(item.priority).dot"
                  />
                  <div class="truncate">
                    <p class="text-xs font-semibold text-stone-800 dark:text-stone-200 truncate">
                      {{ item.title }}
                    </p>
                    <p class="text-[10px] text-stone-400">
                      {{ item.time_ago }}
                    </p>
                  </div>
                </div>
                <ChevronRight
                  :size="14"
                  class="text-stone-400 shrink-0"
                />
              </div>
            </div>
            <div
              v-else
              class="py-6 text-center text-xs text-stone-400"
            >
              No pending approvals
            </div>
          </div>

          <!-- Stay on Top Banner -->
          <div class="bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40 rounded-2xl p-5">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
                <Zap :size="16" />
              </div>
              <div>
                <h4 class="font-semibold text-sm text-stone-900 dark:text-stone-100">
                  Stay on top of what matters
                </h4>
                <p class="mt-1 text-xs text-stone-500 dark:text-stone-400 leading-relaxed">
                  Enable notifications to get alerted about urgent decisions.
                </p>
                <button class="mt-3.5 w-full py-2 rounded-lg bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-700 text-xs font-semibold text-stone-800 dark:text-stone-200 hover:bg-stone-50 dark:hover:bg-stone-800 shadow-sm transition">
                  Manage notifications
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- NEW DECISION MODAL -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 z-50 bg-stone-950/50 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl p-6 w-full max-w-lg shadow-xl space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-stone-100 dark:border-stone-800">
          <h3 class="font-bold text-base text-stone-900 dark:text-stone-100">
            Create decision task
          </h3>
          <button
            class="text-stone-400 hover:text-stone-600"
            @click="showCreateModal = false"
          >
            <X :size="18" />
          </button>
        </div>

        <form
          class="space-y-3.5"
          @submit.prevent="handleCreateDecision"
        >
          <div>
            <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Title</label>
            <input
              v-model="newDecision.title"
              required
              placeholder="e.g. Approve campaign brief"
              class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Subtitle</label>
            <input
              v-model="newDecision.subtitle"
              placeholder="e.g. Launch-ready campaign for Q2 product release"
              class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            >
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Priority</label>
              <select
                v-model="newDecision.priority"
                class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="urgent">
                  Urgent
                </option>
                <option value="high">
                  High priority
                </option>
                <option value="medium">
                  Medium risk
                </option>
                <option value="low">
                  Low risk
                </option>
                <option value="normal">
                  Normal
                </option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Confidence Score (%)</label>
              <input
                v-model.number="newDecision.confidence_score"
                type="number"
                min="1"
                max="100"
                class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              >
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Agent Name</label>
              <input
                v-model="newDecision.agent_name"
                required
                placeholder="e.g. Nova"
                class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              >
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Agent Role</label>
              <input
                v-model="newDecision.agent_role"
                required
                placeholder="e.g. Marketing agent"
                class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              >
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Summary</label>
            <textarea
              v-model="newDecision.summary"
              rows="2"
              placeholder="Executive summary of the decision context..."
              class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Key Rationale (1 per line)</label>
            <textarea
              v-model="newDecision.key_rationale_text"
              rows="2"
              placeholder="Aligned with product positioning..."
              class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 dark:text-stone-300 mb-1">Potential Risks (1 per line)</label>
            <textarea
              v-model="newDecision.potential_risks_text"
              rows="2"
              placeholder="Higher-than-expected CPC in paid channels..."
              class="w-full px-3 py-2 rounded-lg border border-stone-200 dark:border-stone-700 bg-transparent text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div class="pt-3 border-t border-stone-100 dark:border-stone-800 flex items-center justify-end gap-2.5">
            <button
              type="button"
              class="px-4 py-2 rounded-lg border border-stone-200 dark:border-stone-700 text-xs font-semibold text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-800 transition"
              @click="showCreateModal = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition disabled:opacity-50"
              :disabled="createSubmitting"
            >
              {{ createSubmitting ? 'Saving...' : 'Save Decision' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
