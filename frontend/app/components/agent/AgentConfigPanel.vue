<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  Settings2,
  Edit2,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle,
  X,
  KeyRound,
  Cpu,
  Bot
} from '@lucide/vue'
import { useApi } from '~/composables/useApi'

interface AgentConfig {
  base_url: string
  model: string
  max_rounds: number
  workspace: string
  system_prompt_append: string
  api_key_set: boolean
}

const api = useApi()

// ── State ────────────────────────────────────────────────────────────────────
const config = ref<AgentConfig | null>(null)
const loading = ref(true)
const fetchError = ref<string | null>(null)
const toast = ref<{ type: 'success' | 'error', message: string } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

// Edit modal
const showModal = ref(false)
const saving = ref(false)
const form = reactive({
  base_url: '',
  api_key: '',
  model: '',
  max_rounds: 8,
  workspace: '',
  system_prompt_append: ''
})

// Reset confirm
const showResetConfirm = ref(false)
const resetting = ref(false)

// ── Fetch ─────────────────────────────────────────────────────────────────────
async function fetchConfig() {
  loading.value = true
  fetchError.value = null
  try {
    config.value = await api.agentConfig.get() as AgentConfig
  } catch (e: any) {
    fetchError.value = e?.data?.message ?? e?.message ?? 'Failed to load agent configuration.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchConfig)

// ── Toast helper ─────────────────────────────────────────────────────────────
function showToast(type: 'success' | 'error', message: string) {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { type, message }
  toastTimer = setTimeout(() => (toast.value = null), 3500)
}

// ── Edit modal ────────────────────────────────────────────────────────────────
function openModal() {
  if (!config.value) return
  form.base_url = config.value.base_url ?? ''
  form.api_key = ''
  form.model = config.value.model ?? ''
  form.max_rounds = config.value.max_rounds ?? 8
  form.workspace = config.value.workspace ?? ''
  form.system_prompt_append = config.value.system_prompt_append ?? ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function saveConfig() {
  saving.value = true
  try {
    const payload: Record<string, any> = {
      base_url: form.base_url,
      model: form.model,
      max_rounds: form.max_rounds,
      workspace: form.workspace,
      system_prompt_append: form.system_prompt_append
    }
    // Only send api_key if the user typed something (write-only field)
    if (form.api_key.trim()) {
      payload.api_key = form.api_key.trim()
    }
    config.value = await api.agentConfig.update(payload) as AgentConfig
    closeModal()
    showToast('success', 'Configuration saved successfully.')
  } catch (e: any) {
    showToast('error', e?.data?.message ?? e?.message ?? 'Failed to save configuration.')
  } finally {
    saving.value = false
  }
}

// ── Reset ─────────────────────────────────────────────────────────────────────
async function confirmReset() {
  resetting.value = true
  try {
    const result = await api.agentConfig.reset() as { ok: boolean, message: string }
    showResetConfirm.value = false
    await fetchConfig()
    showToast('success', result.message ?? 'Configuration reset to defaults.')
  } catch (e: any) {
    showToast('error', e?.data?.message ?? e?.message ?? 'Failed to reset configuration.')
  } finally {
    resetting.value = false
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function truncate(str: string, max = 60) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '…' : str
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Bot
          :size="18"
          class="text-blue-500"
        />
        <h2 class="text-sm font-semibold text-stone-900 dark:text-stone-100 uppercase tracking-wider">
          Agent Configuration
        </h2>
      </div>
      <button
        v-if="!loading && !fetchError"
        class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
        @click="openModal"
      >
        <Edit2 :size="15" />
        Edit Configuration
      </button>
    </div>

    <!-- Toast -->
    <Transition name="fade">
      <div
        v-if="toast"
        :class="[
          'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium border',
          toast.type === 'success'
            ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
            : 'bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300'
        ]"
      >
        <CheckCircle
          v-if="toast.type === 'success'"
          :size="16"
          class="shrink-0"
        />
        <AlertCircle
          v-else
          :size="16"
          class="shrink-0"
        />
        {{ toast.message }}
      </div>
    </Transition>

    <!-- Error banner -->
    <div
      v-if="fetchError"
      class="flex items-center gap-3 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300"
    >
      <AlertCircle
        :size="16"
        class="shrink-0"
      />
      {{ fetchError }}
    </div>

    <!-- Loading skeleton -->
    <div
      v-else-if="loading"
      class="rounded-2xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 p-5 space-y-3"
    >
      <div
        v-for="i in 5"
        :key="i"
        class="h-4 rounded-lg bg-stone-100 dark:bg-stone-800 animate-pulse"
        :style="{ width: `${55 + i * 8}%` }"
      />
    </div>

    <!-- Config card -->
    <div
      v-else-if="config"
      class="rounded-2xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 overflow-hidden shadow-sm"
    >
      <dl class="divide-y divide-stone-100 dark:divide-stone-800">
        <!-- LLM Endpoint -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-start">
          <dt class="flex items-center gap-1.5 text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1 pt-0.5">
            <Settings2 :size="13" /> LLM Endpoint
          </dt>
          <dd class="col-span-2 text-sm text-stone-800 dark:text-stone-200 font-mono break-all">
            {{ config.base_url || '—' }}
          </dd>
        </div>

        <!-- Model -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-start">
          <dt class="flex items-center gap-1.5 text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1 pt-0.5">
            <Cpu :size="13" /> Model
          </dt>
          <dd class="col-span-2 text-sm text-stone-800 dark:text-stone-200 font-mono">
            {{ config.model || '—' }}
          </dd>
        </div>

        <!-- Max Rounds -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-center">
          <dt class="text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1">
            Max Rounds
          </dt>
          <dd class="col-span-2 text-sm text-stone-800 dark:text-stone-200">
            {{ config.max_rounds }}
          </dd>
        </div>

        <!-- Workspace -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-start">
          <dt class="text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1 pt-0.5">
            Workspace
          </dt>
          <dd class="col-span-2 text-sm text-stone-800 dark:text-stone-200 font-mono break-all">
            {{ config.workspace || '—' }}
          </dd>
        </div>

        <!-- API Key (write-only indicator) -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-center">
          <dt class="flex items-center gap-1.5 text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1">
            <KeyRound :size="13" /> API Key
          </dt>
          <dd class="col-span-2">
            <span
              v-if="config.api_key_set"
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
            >
              <CheckCircle :size="11" /> Key configured
            </span>
            <span
              v-else
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
            >
              <AlertCircle :size="11" /> No key set
            </span>
          </dd>
        </div>

        <!-- System Prompt Append -->
        <div class="grid grid-cols-3 gap-4 px-5 py-3.5 items-start">
          <dt class="text-xs font-semibold text-stone-500 uppercase tracking-wider col-span-1 pt-0.5">
            Prompt Append
          </dt>
          <dd class="col-span-2 text-sm text-stone-400 dark:text-stone-500 italic">
            {{ config.system_prompt_append ? truncate(config.system_prompt_append) : '(none)' }}
          </dd>
        </div>
      </dl>

      <!-- Card footer -->
      <div class="px-5 py-3 border-t border-stone-100 dark:border-stone-800 flex justify-end">
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 transition-colors"
          @click="showResetConfirm = true"
        >
          <RotateCcw :size="14" />
          Reset to Defaults
        </button>
      </div>
    </div>

    <!-- Reset confirm overlay -->
    <Transition name="fade">
      <div
        v-if="showResetConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
        @click.self="showResetConfirm = false"
      >
        <div class="relative w-full max-w-sm p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl space-y-4">
          <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100">
            Reset to Defaults?
          </h3>
          <p class="text-sm text-stone-500 dark:text-stone-400 leading-relaxed">
            This will clear all custom configuration and restore agent settings from environment variables. This action cannot be undone.
          </p>
          <div class="flex justify-end gap-2 pt-1">
            <button
              class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 transition-colors"
              @click="showResetConfirm = false"
            >
              Cancel
            </button>
            <button
              :disabled="resetting"
              class="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-medium shadow-sm transition-all disabled:opacity-60"
              @click="confirmReset"
            >
              <RotateCcw
                :size="15"
                :class="{ 'animate-spin': resetting }"
              />
              {{ resetting ? 'Resetting…' : 'Reset' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit modal -->
    <Transition name="fade">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
        @click.self="closeModal"
      >
        <div class="relative w-full max-w-xl p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl">
          <!-- Modal header -->
          <div class="flex items-center justify-between pb-4 border-b border-stone-100 dark:border-stone-800">
            <div class="flex items-center gap-2">
              <Settings2
                :size="18"
                class="text-blue-500"
              />
              <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100">
                Edit Agent Configuration
              </h3>
            </div>
            <button
              class="p-1.5 rounded-lg hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 transition-colors"
              @click="closeModal"
            >
              <X :size="18" />
            </button>
          </div>

          <!-- Form -->
          <form
            class="mt-5 space-y-4"
            @submit.prevent="saveConfig"
          >
            <!-- LLM Endpoint -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                LLM Endpoint
              </label>
              <input
                v-model="form.base_url"
                type="text"
                placeholder="http://localhost:11434/v1"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- API Key -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                API Key
              </label>
              <input
                v-model="form.api_key"
                type="password"
                autocomplete="new-password"
                placeholder="Leave blank to keep existing key"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- Model -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Model
              </label>
              <input
                v-model="form.model"
                type="text"
                placeholder="llama3.1"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- Max Rounds -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Max Rounds <span class="text-stone-400 normal-case font-normal">(1–20)</span>
              </label>
              <input
                v-model.number="form.max_rounds"
                type="number"
                min="1"
                max="20"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- Workspace Path -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Workspace Path
              </label>
              <input
                v-model="form.workspace"
                type="text"
                placeholder="/path/to/workspace"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <!-- System Prompt Append -->
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                System Prompt Append
              </label>
              <textarea
                v-model="form.system_prompt_append"
                rows="3"
                placeholder="Extra instructions appended to the agent system prompt. E.g. Always respond in formal English."
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
              />
            </div>

            <!-- Footer -->
            <div class="flex justify-end gap-2 pt-3 border-t border-stone-100 dark:border-stone-800">
              <button
                type="button"
                class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-sm font-medium text-stone-700 dark:text-stone-300 transition-colors"
                @click="closeModal"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:scale-100"
              >
                <Save :size="15" />
                {{ saving ? 'Saving…' : 'Save Configuration' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
