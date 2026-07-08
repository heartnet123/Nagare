<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { Agent, Skill } from '~/types'
import { Bot, Activity, Plus, X, Save, AlertCircle, CheckCircle, Cpu, Hammer } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const api = useApi()

// State
const agents = ref<any[]>([])
const skills = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const successMsg = ref<string | null>(null)

// Form state
const showForm = ref(false)
const saving = ref(false)
const form = reactive({
  name: '',
  model: 'llama3.1',
  type: 'chat' as 'chat' | 'rag' | 'search',
  status: 'active' as 'active' | 'inactive',
  system_prompt: '',
  skills: [] as string[]
})

// Metrics computation
const totalAgents = computed(() => agents.value.length)
const activeAgents = computed(() => agents.value.filter(a => a.status === 'active').length)
const avgLatency = computed(() => {
  if (agents.value.length === 0) return '0ms'
  const sum = agents.value.reduce((acc, a) => acc + (a.latency || 0), 0)
  return `${Math.round(sum / agents.value.length)}ms`
})
const totalRequests = computed(() => {
  const sum = agents.value.reduce((acc, a) => acc + (a.requests || 0), 0)
  return sum >= 1000 ? `${(sum / 1000).toFixed(1)}K` : sum.toString()
})

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const [agentsData, skillsData] = await Promise.all([
      api.agents.list(),
      api.agents.listSkills()
    ])
    agents.value = agentsData as any[]
    skills.value = skillsData as any[]
  } catch (err: any) {
    error.value = err.message || 'Failed to load agents or skills data.'
  } finally {
    loading.value = false
  }
}

function openAddForm() {
  form.name = ''
  form.model = 'llama3.1'
  form.type = 'chat'
  form.status = 'active'
  form.system_prompt = ''
  form.skills = []
  showForm.value = true
  successMsg.value = null
  error.value = null
}

async function saveAgent() {
  error.value = null
  successMsg.value = null

  if (!form.name.trim()) {
    error.value = 'Agent name is required'
    return
  }

  saving.value = true
  try {
    await api.agents.create({
      name: form.name.trim(),
      model: form.model.trim(),
      type: form.type,
      status: form.status,
      system_prompt: form.system_prompt.trim(),
      skills: form.skills
    })
    successMsg.value = `Agent "${form.name}" created successfully.`
    showForm.value = false
    await fetchData()
  } catch (err: any) {
    error.value = err.data?.detail || err.message || 'Failed to create agent'
  } finally {
    saving.value = false
  }
}

function toggleSkill(skillName: string) {
  const index = form.skills.indexOf(skillName)
  if (index === -1) {
    form.skills.push(skillName)
  } else {
    form.skills.splice(index, 1)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Agents"
      description="The autonomous workers that power your pipeline. Monitor, configure, and deploy new agents."
    >
      <template #action>
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
          @click="openAddForm"
        >
          <Plus :size="16" />
          Create Agent
        </button>
      </template>
    </DashboardPageHeader>

    <!-- Error/Success Banners -->
    <div v-if="error" class="mb-6 flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400 text-sm">
      <AlertCircle :size="18" />
      <span>{{ error }}</span>
    </div>

    <div v-if="successMsg" class="mb-6 flex items-center gap-3 p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-400 text-sm">
      <CheckCircle :size="18" />
      <span>{{ successMsg }}</span>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="Bot"
        label="Total Agents"
        :value="totalAgents.toString()"
      />
      <DashboardStatCard
        :icon="Activity"
        label="Active Agents"
        :value="activeAgents.toString()"
        tone="emerald"
      />
      <DashboardStatCard
        :icon="Activity"
        label="Avg. Latency"
        :value="avgLatency"
      />
      <DashboardStatCard
        :icon="Activity"
        label="Total Requests"
        :value="totalRequests"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading && agents.length === 0" class="flex flex-col items-center justify-center py-20 text-stone-400">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3" />
      <span class="text-sm">Loading agents...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="agents.length === 0" class="flex flex-col items-center justify-center p-12 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-center mb-8">
      <Bot :size="48" class="text-stone-300 dark:text-stone-700 mb-3" />
      <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100">No Agents Configured</h4>
      <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 max-w-[280px]">
        Create agents to customize models, rules, prompts, and tool access for specific tasks.
      </p>
      <button
        class="mt-4 px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-xs font-semibold text-stone-700 dark:text-stone-300 transition-colors"
        @click="openAddForm"
      >
        Configure Your First Agent
      </button>
    </div>

    <!-- Agents Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div
        v-for="a in agents"
        :key="a.id"
        class="flex flex-col justify-between p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm hover:shadow-md transition-all group"
      >
        <div>
          <!-- Title & Badges -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400">
                <Bot :size="20" />
              </div>
              <div>
                <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
                  {{ a.name }}
                </h4>
                <div class="flex items-center gap-1.5 mt-1 text-[10px] font-semibold">
                  <span class="px-1.5 py-0.5 rounded bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 uppercase font-mono">
                    {{ a.type }}
                  </span>
                  <span class="text-stone-400">•</span>
                  <span class="font-mono text-stone-500">{{ a.model }}</span>
                </div>
              </div>
            </div>
            <DashboardBadge
              :tone="a.status === 'active' ? 'emerald' : 'neutral'"
            >
              {{ a.status === 'active' ? 'Active' : 'Inactive' }}
            </DashboardBadge>
          </div>

          <!-- Prompt & Skills -->
          <div class="mt-4 pt-3 border-t border-stone-100 dark:border-stone-800/80 space-y-2">
            <p v-if="a.system_prompt" class="text-xs text-stone-500 dark:text-stone-400 leading-relaxed italic line-clamp-2">
              "{{ a.system_prompt }}"
            </p>
            <p v-else class="text-xs text-stone-400 dark:text-stone-600 italic">
              No custom system prompt configured.
            </p>

            <!-- Skills List -->
            <div v-if="a.skills && a.skills.length" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="skill in a.skills"
                :key="skill"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/30 border border-blue-100/50 dark:border-blue-900/30 text-[10px] font-semibold text-blue-700 dark:text-blue-400"
              >
                <Hammer :size="10" />
                {{ skill }}
              </span>
            </div>
          </div>
        </div>

        <!-- Latency & Stats -->
        <div class="flex items-center justify-between gap-4 mt-4 pt-3 border-t border-stone-100 dark:border-stone-800/80 text-xs">
          <div class="flex gap-6 text-xs">
            <div class="flex flex-col">
              <span class="text-stone-400">Total Requests</span>
              <span class="font-semibold text-stone-800 dark:text-stone-200">
                {{ (a.requests || 0).toLocaleString() }}
              </span>
            </div>
            <div class="flex flex-col">
              <span class="text-stone-400">Avg. Latency</span>
              <span class="font-semibold text-stone-800 dark:text-stone-200">
                {{ a.latency ? `${Math.round(a.latency)}ms` : '—' }}
              </span>
            </div>
          </div>
          <div class="w-24 h-8 opacity-60">
            <!-- Sparkline placeholder using mock load trends -->
            <DashboardSparkline
              :data="[15, 20, 18, 30, a.status === 'active' ? 45 : 0, a.status === 'active' ? 32 : 0, a.status === 'active' ? 40 : 0]"
              :color="a.status === 'active' ? '#3b82f6' : '#a8a29e'"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Agent Config Panel -->
    <div class="mt-10 pt-8 border-t border-stone-200 dark:border-stone-800">
      <AgentAgentConfigPanel />
    </div>

    <!-- Sliding Modal Form / Panel -->
    <Transition name="fade">
      <div
        v-if="showForm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
        @click.self="showForm = false"
      >
        <div
          class="relative w-full max-w-lg p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl space-y-6"
        >
          <div class="flex items-center justify-between pb-3 border-b border-stone-100 dark:border-stone-800">
            <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <Bot :size="18" class="text-blue-500" />
              Create Custom Agent
            </h3>
            <button
              class="p-1 rounded-lg text-stone-400 hover:text-stone-800 dark:hover:text-stone-100"
              @click="showForm = false"
            >
              <X :size="20" />
            </button>
          </div>

          <form
            class="space-y-4"
            @submit.prevent="saveAgent"
          >
            <!-- Agent Name -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Agent Name
              </label>
              <input
                v-model="form.name"
                type="text"
                required
                placeholder="e.g. Code Reviewer"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- Agent Model -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Agent Model
              </label>
              <input
                v-model="form.model"
                type="text"
                required
                placeholder="e.g. llama3.1, gpt-4o, claude-3-5-sonnet"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- Agent Type & Status -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Agent Type
                </label>
                <select
                  v-model="form.type"
                  class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                >
                  <option value="chat">Chat</option>
                  <option value="rag">RAG</option>
                  <option value="search">Search</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                  Initial Status
                </label>
                <select
                  v-model="form.status"
                  class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            <!-- Agent System Prompt -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Agent System Prompt
              </label>
              <textarea
                v-model="form.system_prompt"
                rows="4"
                placeholder="Give your agent custom rules, personality, or guidelines here..."
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
              />
            </div>

            <!-- Agent Skills -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Enabled Skills
              </label>
              <div
                v-if="skills.length"
                class="grid grid-cols-2 gap-2 mt-1.5"
              >
                <button
                  v-for="skill in skills"
                  :key="skill.name"
                  type="button"
                  class="flex items-center gap-2 p-2.5 rounded-xl border text-left transition-all"
                  :class="[
                    form.skills.includes(skill.name)
                      ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400'
                      : 'border-stone-200 dark:border-stone-800 text-stone-700 dark:text-stone-400 hover:bg-stone-50 dark:hover:bg-stone-850'
                  ]"
                  @click="toggleSkill(skill.name)"
                >
                  <Hammer :size="14" />
                  <div>
                    <div class="text-xs font-semibold">{{ skill.name }}</div>
                    <div class="text-[10px] opacity-75 truncate max-w-[150px]">{{ skill.title }}</div>
                  </div>
                </button>
              </div>
              <p v-else class="text-xs text-stone-400 dark:text-stone-600 italic mt-1">
                No custom skills found in the backend.
              </p>
            </div>

            <div class="flex justify-end gap-3 pt-4 border-t border-stone-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 transition-colors"
                @click="showForm = false"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-colors"
              >
                <Save :size="16" />
                {{ saving ? 'Creating...' : 'Create Agent' }}
              </button>
            </div>
          </form>
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
