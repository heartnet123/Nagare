<script setup lang="ts">
import { useApiAgents } from '~/composables/useApi/agents'
import type { Agent } from '~/types'

definePageMeta({ layout: 'default', path: '/agents/create' })
useHead({ title: 'Create agent | Nagare' })

const api = useApiAgents()
const saving = ref(false)
const error = ref('')
const form = reactive({
  name: '', role_title: '', category: 'Custom', model: 'llama3.1',
  description: '', system_prompt: '', status: 'active' as Agent['status'],
  type: 'chat' as Agent['type'], tagsInput: '', capabilitiesInput: '', toolsInput: ''
})
const categories = ['Research', 'Writing', 'Design', 'Analysis', 'Automation', 'Productivity', 'Marketing', 'Custom']
const presets = [
  { name: 'Research', icon: 'i-lucide-search' },
  { name: 'Writing', icon: 'i-lucide-pen-line' },
  { name: 'Analysis', icon: 'i-lucide-chart-no-axes-combined' },
  { name: 'Automation', icon: 'i-lucide-workflow' },
  { name: 'Support', icon: 'i-lucide-headphones' }
]
const tools = computed(() => form.toolsInput.split(',').map(s => s.trim()).filter(Boolean))
const capabilities = computed(() => form.capabilitiesInput.split('\n').map(s => s.trim()).filter(Boolean))

function selectPreset(name: string) {
  form.role_title = name
  form.category = categories.includes(name) ? name : 'Custom'
}

async function saveAgent() {
  if (saving.value) return
  error.value = ''
  if (!form.name.trim() || !form.model.trim()) {
    error.value = 'Agent name and model are required.'
    return
  }
  saving.value = true
  try {
    const created = await api.create({
      name: form.name.trim(), role_title: form.role_title.trim(), category: form.category,
      model: form.model.trim(), description: form.description.trim(),
      system_prompt: form.system_prompt.trim(), status: form.status, type: form.type,
      tags: form.tagsInput.split(',').map(s => s.trim()).filter(Boolean),
      capabilities: capabilities.value, tools: tools.value, uses_count: 0, completion_rate: 100
    })
    await navigateTo({ path: '/agents', query: { created: created.id } })
  } catch (err: unknown) {
    const e = err as { data?: { detail?: unknown }, message?: string }
    error.value = typeof e.data?.detail === 'string' ? e.data.detail : e.message || 'Failed to create agent. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <DashboardPageScroll>
    <div class="mx-auto w-full max-w-6xl px-4 py-6 sm:px-8">
      <UButton
        to="/agents"
        icon="i-lucide-arrow-left"
        label="Agents"
        color="neutral"
        variant="link"
        class="mb-4 p-0"
      />
      <header class="mb-8">
        <h1 class="text-2xl font-semibold">
          Create agent
        </h1>
        <p class="mt-1 text-sm text-muted">
          Create an AI teammate tailored to your workflow.
        </p>
      </header>

      <form
        class="agent-form"
        @submit.prevent="saveAgent"
      >
        <fieldset
          :disabled="saving"
          class="min-w-0"
        >
          <nav
            aria-label="Agent setup sections"
            class="mb-8 flex flex-wrap gap-x-6 gap-y-3 border-b border-default pb-4 text-sm"
          >
            <a
              v-for="(section, index) in ['Basics', 'Tools', 'Instructions', 'Review']"
              :key="section"
              :href="`#${section.toLowerCase()}`"
              class="inline-flex items-center gap-2 hover:text-primary"
            >
              <span class="flex size-6 items-center justify-center rounded-full bg-elevated text-xs">{{ index + 1 }}</span>
              {{ section }}
            </a>
          </nav>

          <div class="grid min-w-0 gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
            <div class="min-w-0 space-y-8">
              <section
                id="basics"
                class="scroll-mt-6 space-y-5"
              >
                <h2 class="text-base font-semibold">
                  Basics
                </h2>
                <label>Agent name <span class="text-error">*</span>
                  <input
                    v-model="form.name"
                    name="name"
                    required
                    pattern=".*\S.*"
                    placeholder="e.g. Market Research Assistant"
                  >
                </label>
                <div class="grid gap-4 sm:grid-cols-2">
                  <label>Role / specialty
                    <input
                      v-model="form.role_title"
                      name="role_title"
                      placeholder="Select role or enter your own"
                      list="agent-roles"
                    >
                    <datalist id="agent-roles"><option
                      v-for="category in categories"
                      :key="category"
                      :value="category"
                    /></datalist>
                  </label>
                  <label>Category
                    <select
                      v-model="form.category"
                      name="category"
                    ><option
                      v-for="category in categories"
                      :key="category"
                    >{{ category }}</option></select>
                  </label>
                </div>
                <label>Description (optional)
                  <textarea
                    v-model="form.description"
                    name="description"
                    rows="3"
                    placeholder="What should this agent do?"
                  />
                </label>
                <div>
                  <h3 class="mb-3 text-sm font-medium">
                    Or start with a preset
                  </h3>
                  <div class="flex flex-wrap gap-2">
                    <UButton
                      v-for="preset in presets"
                      :key="preset.name"
                      :icon="preset.icon"
                      :label="preset.name"
                      color="neutral"
                      :variant="form.role_title === preset.name ? 'solid' : 'outline'"
                      :aria-pressed="form.role_title === preset.name"
                      @click="selectPreset(preset.name)"
                    />
                  </div>
                </div>
                <div class="grid gap-4 sm:grid-cols-3">
                  <label>Model <span class="text-error">*</span>
                    <input
                      v-model="form.model"
                      name="model"
                      required
                      pattern=".*\S.*"
                      placeholder="llama3.1"
                    >
                  </label>
                  <label>Type
                    <select
                      v-model="form.type"
                      name="type"
                    ><option value="chat">Chat</option><option value="rag">RAG</option><option value="search">Search</option></select>
                  </label>
                  <label>Status
                    <select
                      v-model="form.status"
                      name="status"
                    ><option value="active">Active</option><option value="inactive">Inactive</option></select>
                  </label>
                </div>
                <label>Tags (comma separated)
                  <input
                    v-model="form.tagsInput"
                    name="tags"
                    placeholder="Web research, Analysis, Reports"
                  >
                </label>
              </section>

              <section
                id="tools"
                class="scroll-mt-6 space-y-5 border-t border-default pt-6"
              >
                <h2 class="text-base font-semibold">
                  Tools
                </h2>
                <label>Connected tools (comma separated)
                  <input
                    v-model="form.toolsInput"
                    name="tools"
                    placeholder="Search, Notion, Slack"
                  >
                </label>
                <label>Capabilities (one per line)
                  <textarea
                    v-model="form.capabilitiesInput"
                    name="capabilities"
                    rows="3"
                    placeholder="Search and evaluate sources&#10;Summarize key findings"
                  />
                </label>
              </section>

              <section
                id="instructions"
                class="scroll-mt-6 space-y-5 border-t border-default pt-6"
              >
                <h2 class="text-base font-semibold">
                  Instructions
                </h2>
                <label>System prompt (optional)
                  <textarea
                    v-model="form.system_prompt"
                    name="system_prompt"
                    rows="5"
                    placeholder="e.g. Be concise, cite sources, focus on recent information..."
                  />
                </label>
              </section>
            </div>

            <aside
              id="review"
              class="min-w-0 scroll-mt-6 border-t border-default pt-6 lg:border-t-0 lg:border-l lg:pl-8 lg:pt-0"
            >
              <div class="space-y-6 break-words lg:sticky lg:top-6">
                <h2 class="text-base font-semibold">
                  Agent preview
                </h2>
                <div>
                  <UIcon
                    name="i-lucide-bot"
                    class="mb-3 size-10 text-primary"
                  />
                  <h3 class="font-semibold">
                    {{ form.name.trim() || 'Untitled agent' }}
                  </h3>
                  <p class="mt-1 text-xs text-muted">
                    Not created yet
                  </p>
                  <p class="mt-3 text-sm">
                    {{ form.role_title.trim() || 'No role selected' }}
                  </p>
                  <p class="mt-2 whitespace-pre-wrap text-sm text-muted">
                    {{ form.description.trim() || 'No description yet.' }}
                  </p>
                </div>
                <div>
                  <h3 class="mb-3 text-sm font-medium">
                    Capabilities
                  </h3>
                  <ul
                    v-if="capabilities.length"
                    class="space-y-2 text-sm text-muted"
                  >
                    <li
                      v-for="(capability, index) in capabilities"
                      :key="index"
                      class="flex items-start gap-2"
                    >
                      <UIcon
                        name="i-lucide-check"
                        class="mt-0.5 size-4 shrink-0 text-primary"
                      /><span class="min-w-0">{{ capability }}</span>
                    </li>
                  </ul>
                  <p
                    v-else
                    class="text-sm text-muted"
                  >
                    No capabilities added yet.
                  </p>
                </div>
                <div>
                  <h3 class="mb-3 text-sm font-medium">
                    Selected tools
                  </h3>
                  <div
                    v-if="tools.length"
                    class="flex flex-wrap gap-2"
                  >
                    <UBadge
                      v-for="(tool, index) in tools"
                      :key="index"
                      color="neutral"
                      variant="subtle"
                      class="max-w-full whitespace-normal break-all"
                    >
                      {{ tool }}
                    </UBadge>
                  </div>
                  <p
                    v-else
                    class="text-sm text-muted"
                  >
                    No tools selected yet.
                  </p>
                </div>
                <dl class="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-2 border-t border-default pt-4 text-sm">
                  <dt class="text-muted">
                    Model
                  </dt><dd>{{ form.model }}</dd>
                  <dt class="text-muted">
                    Type
                  </dt><dd class="uppercase">
                    {{ form.type }}
                  </dd>
                  <dt class="text-muted">
                    Status
                  </dt><dd class="capitalize">
                    {{ form.status }}
                  </dd>
                </dl>
              </div>
            </aside>
          </div>
        </fieldset>

        <UAlert
          v-if="error"
          role="alert"
          color="error"
          variant="soft"
          :title="error"
          class="mt-6"
        />
        <footer class="mt-8 flex flex-wrap justify-end gap-3 border-t border-default pt-5">
          <UButton
            to="/agents"
            label="Cancel"
            color="neutral"
            variant="outline"
            :disabled="saving"
          />
          <UButton
            type="submit"
            icon="i-lucide-plus"
            :label="saving ? 'Creating...' : 'Create agent'"
            :loading="saving"
            :disabled="saving"
          />
        </footer>
      </form>
    </div>
  </DashboardPageScroll>
</template>

<style scoped>
@reference "~/assets/css/main.css";

.agent-form label {
  @apply block text-sm font-medium;
}
.agent-form input,
.agent-form select,
.agent-form textarea {
  @apply mt-2 block w-full min-w-0 rounded-lg border border-default bg-default px-3 py-2 text-sm font-normal text-highlighted outline-none focus:border-primary focus:ring-2 focus:ring-primary/20;
}
.agent-form textarea {
  @apply resize-y;
}
</style>
