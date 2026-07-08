<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Cpu, Plus, Trash2, Edit2, Play, AlertCircle, CheckCircle, Terminal, X, Save } from '@lucide/vue'
import { useApi } from '~/composables/useApi'

interface McpServer {
  name: string
  command: string
  args: string[]
}

const api = useApi()
const servers = ref<McpServer[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const successMsg = ref<string | null>(null)

// Form state
const showForm = ref(false)
const isEditing = ref(false)
const formName = ref('')
const formCommand = ref('')
const formArgs = ref<string[]>([])
const newArg = ref('')

async function fetchServers() {
  loading.value = true
  error.value = null
  try {
    servers.value = await api.mcp.list()
  } catch (err: any) {
    error.value = err.message || 'Failed to load MCP servers'
  } finally {
    loading.value = false
  }
}

function openAddForm() {
  isEditing.value = false
  formName.value = ''
  formCommand.value = ''
  formArgs.value = []
  newArg.value = ''
  showForm.value = true
  successMsg.value = null
  error.value = null
}

function openEditForm(server: McpServer) {
  isEditing.value = true
  formName.value = server.name
  formCommand.value = server.command
  formArgs.value = [...server.args]
  newArg.value = ''
  showForm.value = true
  successMsg.value = null
  error.value = null
}

function addArgument() {
  if (newArg.value.trim()) {
    formArgs.value.push(newArg.value.trim())
    newArg.value = ''
  }
}

function removeArgument(index: number) {
  formArgs.value.splice(index, 1)
}

async function saveServer() {
  error.value = null
  successMsg.value = null

  if (!formName.value.trim() || !formCommand.value.trim()) {
    error.value = 'Name and Command are required'
    return
  }

  // Name check for new servers
  if (!isEditing.value && !/^[a-zA-Z0-9_\-]+$/.test(formName.value)) {
    error.value = 'Name must only contain letters, numbers, underscores, and dashes'
    return
  }

  try {
    const payload = {
      command: formCommand.value.trim(),
      args: formArgs.value
    }

    if (isEditing.value) {
      await api.mcp.update(formName.value, payload)
      successMsg.value = `Server "${formName.value}" updated successfully.`
    } else {
      await api.mcp.create({
        name: formName.value.trim(),
        ...payload
      })
      successMsg.value = `Server "${formName.value}" created successfully.`
    }

    showForm.value = false
    await fetchServers()
  } catch (err: any) {
    error.value = err.data?.detail || err.message || 'Failed to save MCP server'
  }
}

async function deleteServer(name: string) {
  if (!confirm(`Are you sure you want to delete MCP server "${name}"?`)) return
  error.value = null
  successMsg.value = null
  try {
    await api.mcp.delete(name)
    successMsg.value = `Server "${name}" deleted.`
    await fetchServers()
  } catch (err: any) {
    error.value = err.message || 'Failed to delete MCP server'
  }
}

onMounted(() => {
  fetchServers()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Messages -->
    <div
      v-if="error"
      class="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400 text-sm"
    >
      <AlertCircle :size="18" />
      <span>{{ error }}</span>
    </div>

    <div
      v-if="successMsg"
      class="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 text-emerald-700 dark:text-emerald-400 text-sm"
    >
      <CheckCircle :size="18" />
      <span>{{ successMsg }}</span>
    </div>

    <!-- Toolbar -->
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-stone-500 uppercase tracking-wider">
        Configured MCP Servers
      </h3>
      <button
        class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-all hover:scale-[1.02] active:scale-[0.98]"
        @click="openAddForm"
      >
        <Plus :size="16" />
        Add Server
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="flex flex-col items-center justify-center py-12 text-stone-400"
    >
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3" />
      <span class="text-sm">Loading configurations...</span>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="servers.length === 0 && !showForm"
      class="flex flex-col items-center justify-center p-8 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-center"
    >
      <Cpu
        :size="40"
        class="text-stone-300 dark:text-stone-700 mb-3"
      />
      <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
        No Custom MCP Servers
      </h4>
      <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 max-w-[280px]">
        Add model context protocol servers to extend your AI agent's capabilities with custom tools and resources.
      </p>
      <button
        class="mt-4 px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-xs font-semibold text-stone-700 dark:text-stone-300 transition-colors"
        @click="openAddForm"
      >
        Configure Server
      </button>
    </div>

    <!-- Servers Grid -->
    <div
      v-else
      class="grid grid-cols-1 md:grid-cols-2 gap-4"
    >
      <div
        v-for="server in servers"
        :key="server.name"
        class="flex flex-col justify-between p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm hover:shadow-md transition-all group"
      >
        <div>
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <div class="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400">
                <Cpu :size="20" />
              </div>
              <div>
                <h4 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
                  {{ server.name }}
                </h4>
                <div class="flex items-center gap-1.5 mt-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                  <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Active
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                class="p-1.5 rounded-lg text-stone-400 hover:text-stone-800 dark:hover:text-stone-100 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
                title="Edit Configuration"
                @click="openEditForm(server)"
              >
                <Edit2 :size="14" />
              </button>
              <button
                class="p-1.5 rounded-lg text-stone-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
                title="Delete Server"
                @click="deleteServer(server.name)"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>

          <div class="space-y-2 mt-4 pt-3 border-t border-stone-100 dark:border-stone-800/80">
            <div class="flex items-center gap-2 text-xs">
              <span class="text-stone-400 w-16 shrink-0">Command:</span>
              <code class="px-2 py-0.5 rounded bg-stone-50 dark:bg-stone-950 border border-stone-200/50 dark:border-stone-800 font-mono text-stone-800 dark:text-stone-300">{{ server.command }}</code>
            </div>
            <div class="flex items-start gap-2 text-xs">
              <span class="text-stone-400 w-16 shrink-0 mt-0.5">Arguments:</span>
              <div
                v-if="server.args && server.args.length"
                class="flex flex-wrap gap-1"
              >
                <code
                  v-for="(arg, idx) in server.args"
                  :key="idx"
                  class="px-2 py-0.5 rounded bg-stone-100 dark:bg-stone-950/50 border border-stone-200/20 font-mono text-[11px] text-stone-600 dark:text-stone-400"
                >
                  {{ arg }}
                </code>
              </div>
              <span
                v-else
                class="text-stone-400 italic text-[11px]"
              >None</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sliding Modal Form / Panel -->
    <Transition name="fade">
      <div
        v-if="showForm"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
      >
        <div
          class="relative w-full max-w-lg p-6 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-xl space-y-6"
        >
          <div class="flex items-center justify-between pb-3 border-b border-stone-100 dark:border-stone-800">
            <h3 class="text-base font-semibold text-stone-900 dark:text-stone-100">
              {{ isEditing ? 'Edit MCP Server' : 'Add Custom MCP Server' }}
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
            @submit.prevent="saveServer"
          >
            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Server Name
              </label>
              <input
                v-model="formName"
                type="text"
                required
                :disabled="isEditing"
                placeholder="e.g. gcal-mcp"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
              >
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Executable Command
              </label>
              <input
                v-model="formCommand"
                type="text"
                required
                placeholder="e.g. node, python, uvx, npx"
                class="w-full px-4 py-2.5 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              >
            </div>

            <div>
              <label class="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-1.5">
                Command Arguments
              </label>
              <div class="space-y-2">
                <div
                  v-if="formArgs.length"
                  class="flex flex-wrap gap-1.5 p-2 rounded-xl bg-stone-50 dark:bg-stone-950 border border-stone-200/80 dark:border-stone-850"
                >
                  <span
                    v-for="(arg, idx) in formArgs"
                    :key="idx"
                    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-xs font-mono text-stone-800 dark:text-stone-300"
                  >
                    {{ arg }}
                    <button
                      type="button"
                      class="text-stone-400 hover:text-red-500"
                      @click="removeArgument(idx)"
                    >
                      <X :size="12" />
                    </button>
                  </span>
                </div>

                <div class="flex gap-2">
                  <input
                    v-model="newArg"
                    type="text"
                    placeholder="Add argument"
                    class="flex-1 px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-950 text-sm text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                    @keydown.enter.prevent="addArgument"
                  >
                  <button
                    type="button"
                    class="px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 hover:bg-stone-50 dark:hover:bg-stone-800 text-xs font-semibold text-stone-700 dark:text-stone-300 transition-colors"
                    @click="addArgument"
                  >
                    Add
                  </button>
                </div>
              </div>
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
                class="flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-colors"
              >
                <Save :size="16" />
                Save Server
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
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
