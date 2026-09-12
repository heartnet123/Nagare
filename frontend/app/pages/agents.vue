<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Search,
  Plus,
  Check,
  TrendingUp,
  Users,
  FileText,
  Bot,
  Bell,
  X,
  Edit3,
  Trash2
} from '@lucide/vue'
import type { Agent, Skill } from '~/types'

definePageMeta({
  layout: 'default'
})

const api = useApi()

// Data state
const agents = ref<Agent[]>([])
const skills = ref<Skill[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const route = useRoute()
const selectedAgentId = ref<string | null>(typeof route.query.created === 'string' ? route.query.created : null)

// Search, filter, sort
const searchQuery = ref('')
const activeCategory = ref('All agents')
const sortBy = ref<'popular' | 'newest' | 'name'>('popular')
const categories = [
  'All agents',
  'Research',
  'Writing',
  'Design',
  'Analysis',
  'Automation',
  'Productivity',
  'Marketing',
  'Custom'
]

// Modal & form state
const showModal = ref(false)
const editingAgent = ref<Agent | null>(null)
const saving = ref(false)
const showDeleteConfirm = ref(false)
const agentToDelete = ref<Agent | null>(null)
const deleting = ref(false)

const form = reactive({
  name: '',
  role_title: '',
  category: 'Custom',
  model: 'llama3.1',
  description: '',
  system_prompt: '',
  status: 'active' as 'active' | 'inactive',
  type: 'chat' as 'chat' | 'rag' | 'search',
  tagsInput: '',
  capabilitiesInput: '',
  toolsInput: ''
})

// Current selected agent
const selectedAgent = computed<Agent | null>(() => {
  if (!agents.value.length) return null
  const found = agents.value.find(a => a.id === selectedAgentId.value)
  return found || agents.value[0] || null
})

// Filtered and sorted agents
const filteredAgents = computed(() => {
  let list = [...agents.value]

  if (activeCategory.value !== 'All agents') {
    list = list.filter(a => (a.category || 'Custom').toLowerCase() === activeCategory.value.toLowerCase())
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(a =>
      a.name.toLowerCase().includes(q) ||
      (a.role_title && a.role_title.toLowerCase().includes(q)) ||
      (a.description && a.description.toLowerCase().includes(q)) ||
      (a.tags && a.tags.some(t => t.toLowerCase().includes(q)))
    )
  }

  if (sortBy.value === 'popular') {
    list.sort((a, b) => (b.uses_count || 0) - (a.uses_count || 0))
  } else if (sortBy.value === 'newest') {
    list.sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
  } else if (sortBy.value === 'name') {
    list.sort((a, b) => a.name.localeCompare(b.name))
  }

  return list
})

// Metrics for selected agent & coverage
const activeAgentsCount = computed(() => agents.value.filter(a => a.status === 'active').length)
const pausedAgentsCount = computed(() => agents.value.filter(a => a.status !== 'active').length)
const totalAgentsCount = computed(() => agents.value.length)
const coveragePercentage = computed(() => {
  if (!totalAgentsCount.value) return 0
  return Math.round((activeAgentsCount.value / totalAgentsCount.value) * 100)
})

// Category distribution for skills breakdown
const skillBreakdown = computed(() => {
  if (!agents.value.length) return []
  const counts: Record<string, number> = {}
  for (const a of agents.value) {
    const cat = a.category || 'Custom'
    counts[cat] = (counts[cat] || 0) + 1
  }
  return Object.entries(counts)
    .map(([cat, count]) => ({
      category: cat,
      pct: Math.round((count / agents.value.length) * 100)
    }))
    .sort((a, b) => b.pct - a.pct)
    .slice(0, 3)
})

function getAgentVisual(agent: Agent) {
  const name = agent.name.toLowerCase()
  if (name.includes('atlas')) return { bg: 'bg-stone-900 dark:bg-stone-100', text: 'text-white dark:text-stone-900', symbol: '▲' }
  if (name.includes('nova')) return { bg: 'bg-purple-600', text: 'text-white', symbol: '●' }
  if (name.includes('kairo')) return { bg: 'bg-emerald-600', text: 'text-white', symbol: '■' }
  if (name.includes('muse')) return { bg: 'bg-rose-500', text: 'text-white', symbol: '◆' }
  if (name.includes('orion')) return { bg: 'bg-blue-600', text: 'text-white', symbol: '★' }
  if (name.includes('sora')) return { bg: 'bg-amber-500', text: 'text-white', symbol: '✱' }
  if (name.includes('echo')) return { bg: 'bg-teal-500', text: 'text-white', symbol: '💬' }
  if (name.includes('lyra')) return { bg: 'bg-indigo-600', text: 'text-white', symbol: '✦' }
  return { bg: 'bg-blue-500', text: 'text-white', symbol: '🤖' }
}

function formatUses(count?: number) {
  if (!count) return '0 uses'
  if (count >= 1000) return `${(count / 1000).toFixed(1).replace(/\.0$/, '')}k uses`
  return `${count} uses`
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [agentsData, skillsData] = await Promise.all([
      api.agents.list(),
      api.agents.listSkills()
    ])
    agents.value = agentsData || []
    skills.value = skillsData || []
    if (agents.value.length > 0 && !selectedAgentId.value) {
      selectedAgentId.value = agents.value[0]?.id || null
    }
  } catch (err: unknown) {
    const e = err as { message?: string }
    error.value = e.message || 'Failed to load agents.'
  } finally {
    loading.value = false
  }
}

function selectAgent(id: string) {
  selectedAgentId.value = id
}

function goToCreateAgent() {
  return navigateTo('/agents/create')
}

function openEditModal(agent: Agent) {
  editingAgent.value = agent
  form.name = agent.name
  form.role_title = agent.role_title || ''
  form.category = agent.category || 'Custom'
  form.model = agent.model
  form.description = agent.description || ''
  form.system_prompt = agent.system_prompt || ''
  form.status = agent.status
  form.type = agent.type
  form.tagsInput = (agent.tags || []).join(', ')
  form.capabilitiesInput = (agent.capabilities || []).join('\n')
  form.toolsInput = (agent.tools || []).join(', ')
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingAgent.value = null
}

async function saveAgent() {
  if (!form.name.trim()) return
  saving.value = true
  try {
    const payload: Partial<Agent> = {
      name: form.name.trim(),
      role_title: form.role_title.trim(),
      category: form.category,
      model: form.model.trim(),
      description: form.description.trim(),
      system_prompt: form.system_prompt.trim(),
      status: form.status,
      type: form.type,
      tags: form.tagsInput.split(',').map(s => s.trim()).filter(Boolean),
      capabilities: form.capabilitiesInput.split('\n').map(s => s.trim()).filter(Boolean),
      tools: form.toolsInput.split(',').map(s => s.trim()).filter(Boolean)
    }

    if (!editingAgent.value) return
    await api.agents.update(editingAgent.value.id, payload)
    closeModal()
    await loadData()
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string }; message?: string }
    error.value = e.data?.detail || e.message || 'Failed to save agent.'
  } finally {
    saving.value = false
  }
}

function openDeleteModal(agent: Agent) {
  agentToDelete.value = agent
  showDeleteConfirm.value = true
}

function closeDeleteModal() {
  showDeleteConfirm.value = false
  agentToDelete.value = null
}

async function confirmDelete() {
  if (!agentToDelete.value) return
  deleting.value = true
  try {
    await api.agents.delete(agentToDelete.value.id)
    if (selectedAgentId.value === agentToDelete.value.id) {
      selectedAgentId.value = null
    }
    closeDeleteModal()
    await loadData()
  } catch (err: unknown) {
    const e = err as { message?: string }
    error.value = e.message || 'Failed to delete agent.'
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <DashboardPageScroll>
    <div class="px-8 py-6 max-w-[1700px] mx-auto min-h-screen">
      <!-- Loading State -->
      <div
        v-if="loading && agents.length === 0"
        class="flex flex-col items-center justify-center py-32 text-stone-400"
      >
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3" />
        <span class="text-sm">Loading agents...</span>
      </div>

      <!-- State 1: EMPTY STATE (media_1789176576732.png) -->
      <div
        v-else-if="agents.length === 0"
        class="flex flex-col min-h-[85vh] justify-between"
      >
        <!-- Header -->
        <div class="flex items-start justify-between">
          <div>
            <h1 class="text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
              Agents
            </h1>
            <p class="text-stone-500 dark:text-stone-400 text-sm mt-1">
              Your AI teammates for every kind of work.
            </p>
          </div>

          <div class="flex items-center gap-4">
            <div class="relative hidden sm:block">
              <Search
                :size="16"
                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400"
              />
              <input
                type="text"
                placeholder="Search agents..."
                class="w-64 pl-10 pr-4 py-2 text-sm bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                disabled
              >
            </div>
            <button
              class="p-2 text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 rounded-xl border border-stone-200 dark:border-stone-800"
              aria-label="Notifications"
            >
              <Bell :size="18" />
            </button>
            <button
              class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl shadow-sm transition-all"
              @click="goToCreateAgent"
            >
              <Plus :size="16" />
              Create agent
            </button>
          </div>
        </div>

        <!-- Center Robot Empty Hero -->
        <div class="my-auto flex flex-col items-center justify-center text-center py-16">
          <div class="relative mb-6">
            <div class="w-28 h-28 rounded-full bg-blue-50 dark:bg-blue-950/40 flex items-center justify-center">
              <svg
                width="72"
                height="72"
                viewBox="0 0 72 72"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <circle cx="36" cy="10" r="3.5" fill="#93C5FD" />
                <line x1="36" y1="13" x2="36" y2="20" stroke="#93C5FD" stroke-width="3" stroke-linecap="round" />
                <rect x="14" y="20" width="44" height="34" rx="14" fill="#BFDBFE" />
                <rect x="10" y="31" width="4" height="12" rx="2" fill="#93C5FD" />
                <rect x="58" y="31" width="4" height="12" rx="2" fill="#93C5FD" />
                <circle cx="28" cy="35" r="4" fill="#1E3A8A" />
                <circle cx="44" cy="35" r="4" fill="#1E3A8A" />
                <path d="M31 43C33.5 45 38.5 45 41 43" stroke="#1E3A8A" stroke-width="2.5" stroke-linecap="round" />
              </svg>
            </div>
          </div>

          <h2 class="text-2xl font-bold text-stone-900 dark:text-stone-100">
            No agents yet
          </h2>
          <p class="text-stone-500 dark:text-stone-400 text-sm mt-2 max-w-md">
            Create your first agent to automate work, research, analyze, and more.
          </p>

          <div class="mt-6">
            <button
              class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl shadow-sm transition-all"
              @click="goToCreateAgent"
            >
              Create an agent
            </button>
          </div>
        </div>
      </div>

      <!-- State 2: DATA STATE (media_1789176570841.png) -->
      <div
        v-else
        class="flex flex-col lg:flex-row gap-8 items-start"
      >
        <!-- Main Column -->
        <div class="flex-1 w-full min-w-0">
          <!-- Header -->
          <div class="flex items-start justify-between mb-6">
            <div>
              <h1 class="text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
                Agents
              </h1>
              <p class="text-stone-500 dark:text-stone-400 text-sm mt-1">
                Specialized AI teammates for research, writing, design, analysis, and automation.
              </p>
            </div>
            <div class="text-right hidden sm:block">
              <div class="text-xs font-semibold text-stone-700 dark:text-stone-300">
                Active Workspace
              </div>
              <div class="text-xs text-stone-400">
                {{ totalAgentsCount }} configured {{ totalAgentsCount === 1 ? 'agent' : 'agents' }}
              </div>
            </div>
          </div>

          <!-- Search & Create Bar -->
          <div class="flex items-center gap-3 mb-5">
            <div class="relative flex-1">
              <Search
                :size="16"
                class="absolute left-4 top-1/2 -translate-y-1/2 text-stone-400"
              />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search agents, skills, or use cases..."
                class="w-full pl-11 pr-4 py-2.5 bg-stone-50/70 dark:bg-stone-900/70 border border-stone-200/80 dark:border-stone-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-stone-400"
              >
            </div>
            <button
              class="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-xl shadow-sm transition-all shrink-0"
              @click="goToCreateAgent"
            >
              <Plus :size="16" />
              Create agent
            </button>
          </div>

          <!-- Category Pills & Sort -->
          <div class="flex items-center justify-between gap-4 overflow-x-auto pb-2 mb-6 scrollbar-none">
            <div class="flex items-center gap-2">
              <button
                v-for="cat in categories"
                :key="cat"
                class="px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap"
                :class="[
                  activeCategory === cat
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-stone-100 dark:bg-stone-850 text-stone-600 dark:text-stone-400 hover:bg-stone-200 dark:hover:bg-stone-800'
                ]"
                @click="activeCategory = cat"
              >
                {{ cat }}
              </button>
            </div>

            <!-- Sort Dropdown -->
            <div class="relative shrink-0 flex items-center gap-1.5 text-xs text-stone-500 font-medium">
              <span>Sort:</span>
              <select
                v-model="sortBy"
                class="bg-transparent border-none text-xs font-semibold text-stone-700 dark:text-stone-300 focus:outline-none cursor-pointer pr-4"
              >
                <option value="popular">Popular</option>
                <option value="newest">Newest</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>

          <!-- 3-Column Agent Cards Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            <!-- Individual Agent Card -->
            <div
              v-for="a in filteredAgents"
              :key="a.id"
              class="flex flex-col justify-between p-5 rounded-2xl bg-white dark:bg-stone-900 border transition-all cursor-pointer group hover:shadow-md"
              :class="[
                selectedAgent?.id === a.id
                  ? 'border-blue-500 ring-1 ring-blue-500 shadow-sm'
                  : 'border-stone-200/80 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700'
              ]"
              @click="selectAgent(a.id)"
            >
              <div>
                <!-- Top Row: Icon, Titles & Menu -->
                <div class="flex items-start justify-between gap-3 mb-3">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-11 h-11 rounded-2xl flex items-center justify-center text-lg font-bold shrink-0 shadow-xs"
                      :class="[getAgentVisual(a).bg, getAgentVisual(a).text]"
                    >
                      {{ getAgentVisual(a).symbol }}
                    </div>
                    <div>
                      <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100 leading-tight">
                        {{ a.name }}
                      </h3>
                      <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                        {{ a.role_title || a.category || 'AI Agent' }}
                      </p>
                    </div>
                  </div>

                  <div class="relative flex items-center gap-1">
                    <button
                      class="p-1 rounded-lg text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 transition-colors"
                      title="Edit agent"
                      @click.stop="openEditModal(a)"
                    >
                      <Edit3 :size="15" />
                    </button>
                    <button
                      class="p-1 rounded-lg text-stone-400 hover:text-red-600 transition-colors"
                      title="Delete agent"
                      @click.stop="openDeleteModal(a)"
                    >
                      <Trash2 :size="15" />
                    </button>
                  </div>
                </div>

                <!-- Description -->
                <p class="text-xs text-stone-500 dark:text-stone-400 line-clamp-2 leading-relaxed mb-4 min-h-[32px]">
                  {{ a.description || a.system_prompt || 'No description provided.' }}
                </p>

                <!-- Tags Row -->
                <div class="flex flex-wrap gap-1.5 mb-5 min-h-[24px]">
                  <span
                    v-for="tag in (a.tags || [])"
                    :key="tag"
                    class="px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-[11px] font-medium text-stone-600 dark:text-stone-400"
                  >
                    {{ tag }}
                  </span>
                  <span
                    v-if="!a.tags?.length"
                    class="px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-[11px] font-medium text-stone-400"
                  >
                    {{ a.type || 'chat' }}
                  </span>
                </div>
              </div>

              <!-- Card Footer -->
              <div class="flex items-center justify-between pt-3 border-t border-stone-100 dark:border-stone-800/80 text-xs text-stone-500">
                <div class="flex items-center gap-4 font-medium">
                  <span class="flex items-center gap-1.5">
                    <Users :size="13" class="text-stone-400" />
                    {{ formatUses(a.uses_count) }}
                  </span>
                  <span class="flex items-center gap-1.5">
                    <TrendingUp :size="13" class="text-blue-500" />
                    {{ a.completion_rate ?? 100 }}%
                  </span>
                </div>

                <button
                  class="px-4 py-1.5 rounded-xl text-xs font-semibold transition-colors"
                  :class="[
                    selectedAgent?.id === a.id
                      ? 'bg-blue-600 text-white shadow-xs hover:bg-blue-700'
                      : 'bg-stone-100 dark:bg-stone-800 text-stone-700 dark:text-stone-300 hover:bg-stone-200'
                  ]"
                  @click.stop="selectAgent(a.id)"
                >
                  {{ selectedAgent?.id === a.id ? 'Open' : 'Assign' }}
                </button>
              </div>
            </div>

            <!-- "+ Create your own" Card -->
            <div
              class="flex flex-col justify-between p-5 rounded-2xl border-2 border-dashed border-stone-200 dark:border-stone-800 bg-stone-50/40 dark:bg-stone-900/30 hover:border-blue-400 dark:hover:border-blue-500/50 transition-all cursor-pointer group"
              @click="goToCreateAgent"
            >
              <div>
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-11 h-11 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center text-lg font-bold shrink-0">
                    <Plus :size="20" />
                  </div>
                  <div>
                    <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100 leading-tight">
                      Create your own
                    </h3>
                  </div>
                </div>

                <p class="text-xs text-stone-500 dark:text-stone-400 line-clamp-2 leading-relaxed mb-4">
                  Build a custom agent tailored to your workflows and tools.
                </p>

                <div class="flex flex-wrap gap-1.5 mb-5">
                  <span class="px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-[11px] font-medium text-stone-500">
                    Your data
                  </span>
                  <span class="px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-[11px] font-medium text-stone-500">
                    Your tools
                  </span>
                  <span class="px-2.5 py-1 rounded-lg bg-stone-100 dark:bg-stone-800 text-[11px] font-medium text-stone-500">
                    Your goals
                  </span>
                </div>
              </div>

              <div class="pt-3 border-t border-stone-100 dark:border-stone-800/80">
                <button
                  class="w-full py-1.5 rounded-xl border border-blue-600 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 text-xs font-semibold transition-colors"
                >
                  Create agent
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Detail Inspector Drawer (media_1789176570841.png) -->
        <div
          v-if="selectedAgent"
          class="w-full lg:w-[380px] shrink-0 bg-white dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 rounded-3xl p-6 shadow-sm space-y-6 lg:sticky lg:top-6"
        >
          <!-- Selected Agent Header -->
          <div>
            <div class="flex items-start justify-between gap-3 mb-3">
              <div class="flex items-center gap-3">
                <div
                  class="w-12 h-12 rounded-2xl flex items-center justify-center text-xl font-bold shrink-0 shadow-xs"
                  :class="[getAgentVisual(selectedAgent).bg, getAgentVisual(selectedAgent).text]"
                >
                  {{ getAgentVisual(selectedAgent).symbol }}
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <h2 class="text-lg font-bold text-stone-900 dark:text-stone-100">
                      {{ selectedAgent.name }}
                    </h2>
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-800/40">
                      <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      {{ selectedAgent.status === 'active' ? 'Active' : 'Inactive' }}
                    </span>
                  </div>
                  <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                    {{ selectedAgent.role_title || selectedAgent.category || 'AI Agent' }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-1">
                <button
                  class="p-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 rounded-lg"
                  title="Edit"
                  @click="openEditModal(selectedAgent)"
                >
                  <Edit3 :size="16" />
                </button>
              </div>
            </div>

            <!-- Description -->
            <p class="text-xs text-stone-500 dark:text-stone-400 leading-relaxed mt-3">
              {{ selectedAgent.description || selectedAgent.system_prompt || 'No description configured.' }}
            </p>
          </div>

          <!-- Stats Block -->
          <div class="flex items-center justify-between p-4 rounded-2xl bg-stone-50 dark:bg-stone-850/60 border border-stone-100 dark:border-stone-800">
            <div>
              <div class="text-lg font-bold text-stone-900 dark:text-stone-100">
                {{ formatUses(selectedAgent.uses_count).split(' ')[0] }}
              </div>
              <div class="text-[11px] text-stone-400">
                Total uses
              </div>
            </div>

            <div class="h-8 w-px bg-stone-200 dark:bg-stone-800" />

            <div>
              <div class="text-lg font-bold text-stone-900 dark:text-stone-100">
                {{ selectedAgent.completion_rate ?? 100 }}%
              </div>
              <div class="text-[11px] text-stone-400">
                Completion rate
              </div>
            </div>

            <div class="h-8 w-px bg-stone-200 dark:bg-stone-800" />

            <div>
              <div class="text-xs font-mono font-semibold text-stone-600 dark:text-stone-400">
                {{ selectedAgent.model }}
              </div>
              <div class="text-[11px] text-stone-400">
                Model
              </div>
            </div>
          </div>

          <!-- Capabilities -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-3">
              Capabilities
            </h4>
            <div
              v-if="selectedAgent.capabilities && selectedAgent.capabilities.length"
              class="space-y-2.5"
            >
              <div
                v-for="cap in selectedAgent.capabilities"
                :key="cap"
                class="flex items-start gap-2.5 text-xs text-stone-700 dark:text-stone-300"
              >
                <div class="w-4 h-4 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Check :size="10" stroke-width="3" />
                </div>
                <span>{{ cap }}</span>
              </div>
            </div>
            <p
              v-else
              class="text-xs text-stone-400 italic"
            >
              No specific capabilities configured.
            </p>
          </div>

          <!-- Connected Tools -->
          <div>
            <h4 class="text-xs font-bold uppercase tracking-wider text-stone-400 mb-3">
              Connected tools
            </h4>
            <div
              v-if="selectedAgent.tools && selectedAgent.tools.length"
              class="flex flex-wrap gap-2"
            >
              <span
                v-for="tool in selectedAgent.tools"
                :key="tool"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-850 text-xs font-medium text-stone-700 dark:text-stone-300 shadow-2xs"
              >
                <span class="w-1.5 h-1.5 rounded-full bg-blue-500" />
                {{ tool }}
              </span>
            </div>
            <p
              v-else
              class="text-xs text-stone-400 italic"
            >
              No connected tools.
            </p>
          </div>

          <!-- Recent Wins -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-xs font-bold uppercase tracking-wider text-stone-400">
                Recent wins
              </h4>
            </div>
            <div
              v-if="selectedAgent.recent_wins && selectedAgent.recent_wins.length"
              class="space-y-2.5"
            >
              <div
                v-for="win in selectedAgent.recent_wins"
                :key="win.title"
                class="flex items-center justify-between p-2.5 rounded-xl hover:bg-stone-50 dark:hover:bg-stone-850/50 border border-stone-100 dark:border-stone-800/60 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="p-2 rounded-lg bg-stone-100 dark:bg-stone-800 text-stone-500">
                    <FileText :size="14" />
                  </div>
                  <div>
                    <div class="text-xs font-semibold text-stone-800 dark:text-stone-200 line-clamp-1">
                      {{ win.title }}
                    </div>
                    <div class="text-[10px] text-stone-400">
                      {{ win.time }}
                    </div>
                  </div>
                </div>
                <div class="text-[11px] font-medium text-stone-400 shrink-0">
                  {{ win.date }}
                </div>
              </div>
            </div>
            <p
              v-else
              class="text-xs text-stone-400 italic"
            >
              No recorded activity yet.
            </p>
          </div>

          <!-- Bottom Coverage & Skills Summary -->
          <div class="pt-4 border-t border-stone-100 dark:border-stone-800 grid grid-cols-2 gap-4">
            <!-- Agent Coverage Donut (computed live from actual data) -->
            <div class="p-3 rounded-2xl bg-stone-50/60 dark:bg-stone-850/40 border border-stone-100 dark:border-stone-800">
              <div class="text-[11px] font-bold text-stone-700 dark:text-stone-300 mb-2">
                Agent coverage
              </div>
              <div class="flex items-center gap-3">
                <div class="relative w-14 h-14 shrink-0 flex items-center justify-center">
                  <svg
                    viewBox="0 0 36 36"
                    class="w-14 h-14 -rotate-90"
                  >
                    <circle
                      cx="18"
                      cy="18"
                      r="14"
                      fill="none"
                      class="stroke-stone-200 dark:stroke-stone-800"
                      stroke-width="4"
                    />
                    <circle
                      cx="18"
                      cy="18"
                      r="14"
                      fill="none"
                      stroke="#2563EB"
                      stroke-width="4"
                      :stroke-dasharray="`${coveragePercentage}, 100`"
                      stroke-linecap="round"
                    />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <span class="text-[11px] font-extrabold text-stone-900 dark:text-stone-100 leading-none">
                      {{ activeAgentsCount }}/{{ totalAgentsCount }}
                    </span>
                    <span class="text-[8px] text-stone-400 leading-none mt-0.5">active</span>
                  </div>
                </div>
                <div class="text-[10px] space-y-1 text-stone-500">
                  <div class="flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-blue-600" />
                    <span>Active {{ activeAgentsCount }}</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-stone-400" />
                    <span>Paused {{ pausedAgentsCount }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Categories Breakdown (computed live from actual data) -->
            <div class="p-3 rounded-2xl bg-stone-50/60 dark:bg-stone-850/40 border border-stone-100 dark:border-stone-800">
              <div class="text-[11px] font-bold text-stone-700 dark:text-stone-300 mb-2">
                Categories
              </div>
              <div
                v-if="skillBreakdown.length"
                class="space-y-1.5"
              >
                <div
                  v-for="item in skillBreakdown"
                  :key="item.category"
                >
                  <div class="flex justify-between text-[10px] text-stone-500 mb-0.5">
                    <span class="truncate max-w-[80px]">{{ item.category }}</span>
                    <span class="font-semibold">{{ item.pct }}%</span>
                  </div>
                  <div class="h-1.5 w-full bg-stone-200 dark:bg-stone-800 rounded-full overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full" :style="{ width: `${item.pct}%` }" />
                  </div>
                </div>
              </div>
              <p
                v-else
                class="text-[10px] text-stone-400 italic"
              >
                No category data.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Config Panel Section -->
      <div class="mt-16 pt-8 border-t border-stone-200 dark:border-stone-800">
        <AgentAgentConfigPanel />
      </div>
    </div>

    <!-- Edit Agent Modal -->
    <Transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <div class="relative w-full max-w-xl p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl space-y-5 max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between pb-3 border-b border-stone-100 dark:border-stone-800">
            <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <Bot :size="18" class="text-blue-600" />
              Edit Agent
            </h3>
            <button
              class="p-1 rounded-lg text-stone-400 hover:text-stone-700 dark:hover:text-stone-200"
              @click="closeModal"
            >
              <X :size="18" />
            </button>
          </div>

          <form class="space-y-4" @submit.prevent="saveAgent">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Agent Name
                </label>
                <input
                  v-model="form.name"
                  type="text"
                  required
                  placeholder="e.g. Code Reviewer"
                  class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
              </div>
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Role Title
                </label>
                <input
                  v-model="form.role_title"
                  type="text"
                  placeholder="e.g. Research agent"
                  class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
              </div>
            </div>

            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Category
                </label>
                <select
                  v-model="form.category"
                  class="w-full px-3 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
                >
                  <option v-for="cat in categories.filter(c => c !== 'All agents')" :key="cat" :value="cat">
                    {{ cat }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Model
                </label>
                <input
                  v-model="form.model"
                  type="text"
                  required
                  placeholder="llama3.1"
                  class="w-full px-3 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
                >
              </div>
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Type
                </label>
                <select
                  v-model="form.type"
                  class="w-full px-3 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
                >
                  <option value="chat">Chat</option>
                  <option value="rag">RAG</option>
                  <option value="search">Search</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Description
              </label>
              <input
                v-model="form.description"
                type="text"
                placeholder="What this agent does..."
                class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
              >
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                System Prompt
              </label>
              <textarea
                v-model="form.system_prompt"
                rows="3"
                placeholder="Custom rules, behavior, or instructions..."
                class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm resize-none"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Tags (comma separated)
              </label>
              <input
                v-model="form.tagsInput"
                type="text"
                placeholder="Web research, Analysis, Reports"
                class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
              >
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Connected Tools (comma separated)
              </label>
              <input
                v-model="form.toolsInput"
                type="text"
                placeholder="Search, Notion, Slack"
                class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm"
              >
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Capabilities (one per line)
              </label>
              <textarea
                v-model="form.capabilitiesInput"
                rows="3"
                placeholder="Search and evaluate sources&#10;Summarize key findings"
                class="w-full px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm resize-none"
              />
            </div>

            <div class="flex justify-end gap-3 pt-3 border-t border-stone-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-50"
                @click="closeModal"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm"
              >
                {{ saving ? 'Saving...' : 'Update Agent' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Delete Confirmation Modal -->
    <Transition name="fade">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
        @click.self="closeDeleteModal"
      >
        <div class="relative w-full max-w-md p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl space-y-4">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400">
              <Trash2 :size="20" />
            </div>
            <div>
              <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100">
                Delete Agent
              </h3>
              <p class="text-xs text-stone-500">
                This action cannot be undone.
              </p>
            </div>
          </div>

          <p class="text-sm text-stone-600 dark:text-stone-300">
            Are you sure you want to delete <strong>{{ agentToDelete?.name }}</strong>?
          </p>

          <div class="flex justify-end gap-3 pt-2">
            <button
              class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-50"
              @click="closeDeleteModal"
            >
              Cancel
            </button>
            <button
              :disabled="deleting"
              class="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-medium shadow-sm disabled:opacity-50"
              @click="confirmDelete"
            >
              {{ deleting ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </DashboardPageScroll>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
