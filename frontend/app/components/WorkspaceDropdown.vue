<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ChevronDown, Bot, Cpu, Plus } from '@lucide/vue'
import { useActiveSelection } from '~/composables/useActiveSelection'

const {
  selectedModel,
  selectedAgent,
  models,
  agents,
  loadingModels,
  loadingAgents,
  selectModel,
  selectAgent,
  displayText,
  init
} = useActiveSelection()

const isOpen = ref(false)
const activeTab = ref<'models' | 'agents'>('models')

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.workspace-dropdown')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  init()
})
</script>

<template>
  <div class="relative workspace-dropdown">
    <button
      type="button"
      class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-sm text-xs font-medium text-stone-700 dark:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800 transition-colors select-none"
      @click="toggleDropdown"
    >
      <component
        :is="selectedAgent ? Bot : Cpu"
        :size="14"
        :stroke-width="1.5"
        class="text-stone-500 dark:text-stone-400"
      />
      <span>{{ displayText }}</span>
      <ChevronDown
        :size="12"
        :stroke-width="1.5"
        class="ml-0.5 text-stone-400 transition-transform duration-250"
        :class="{ 'rotate-180': isOpen }"
      />
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute bottom-full right-0 mb-2 w-80 bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl shadow-lg overflow-hidden z-50"
      >
        <!-- Tabs -->
        <div class="flex border-b border-stone-200 dark:border-stone-800">
          <button
            type="button"
            class="flex-1 px-4 py-3 text-sm font-medium transition-colors"
            :class="[
              activeTab === 'models'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-500 bg-blue-50/50 dark:bg-blue-950/20'
                : 'text-stone-500 hover:text-stone-700 dark:hover:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/50'
            ]"
            @click="activeTab = 'models'"
          >
            <div class="flex items-center justify-center gap-2">
              <Cpu :size="16" />
              Models
            </div>
          </button>
          <button
            type="button"
            class="flex-1 px-4 py-3 text-sm font-medium transition-colors"
            :class="[
              activeTab === 'agents'
                ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-500 bg-blue-50/50 dark:bg-blue-950/20'
                : 'text-stone-500 hover:text-stone-700 dark:hover:text-stone-300 hover:bg-stone-50 dark:hover:bg-stone-800/50'
            ]"
            @click="activeTab = 'agents'"
          >
            <div class="flex items-center justify-center gap-2">
              <Bot :size="16" />
              Agents
            </div>
          </button>
        </div>

        <!-- Models Tab -->
        <div
          v-if="activeTab === 'models'"
          class="max-h-64 overflow-y-auto"
        >
          <div
            v-if="loadingModels"
            class="p-4 text-center text-stone-400 text-sm"
          >
            Loading models...
          </div>
          <div
            v-else-if="models.length === 0"
            class="p-4 text-center text-stone-400 text-sm"
          >
            No models available
          </div>
          <div
            v-else
            class="p-2"
          >
            <button
              v-for="model in models"
              :key="model.id"
              type="button"
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors"
              :class="[
                selectedModel?.id === model.id
                  ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400'
                  : 'hover:bg-stone-50 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300'
              ]"
              @click="selectModel(model)"
            >
              <div class="p-2 rounded-lg bg-stone-100 dark:bg-stone-800">
                <Cpu
                  :size="16"
                  class="text-stone-500"
                />
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">
                  {{ model.name }}
                </div>
                <div class="text-xs text-stone-400 truncate">
                  {{ model.provider }}
                </div>
              </div>
              <div
                v-if="selectedModel?.id === model.id"
                class="text-blue-500"
              >
                <svg
                  class="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </button>
          </div>
        </div>

        <!-- Agents Tab -->
        <div
          v-if="activeTab === 'agents'"
          class="max-h-64 overflow-y-auto"
        >
          <div
            v-if="loadingAgents"
            class="p-4 text-center text-stone-400 text-sm"
          >
            Loading agents...
          </div>
          <div
            v-else-if="agents.length === 0"
            class="p-4"
          >
            <div class="text-center">
              <Bot
                :size="32"
                class="mx-auto text-stone-300 dark:text-stone-600 mb-2"
              />
              <p class="text-sm text-stone-500 dark:text-stone-400 mb-3">
                No agents created yet
              </p>
              <NuxtLink
                to="/agents"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                @click="isOpen = false"
              >
                <Plus :size="16" />
                Create your own agent
              </NuxtLink>
            </div>
          </div>
          <div
            v-else
            class="p-2"
          >
            <button
              v-for="agent in agents"
              :key="agent.id"
              type="button"
              class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors"
              :class="[
                selectedAgent?.id === agent.id
                  ? 'bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400'
                  : 'hover:bg-stone-50 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300'
              ]"
              @click="selectAgent(agent)"
            >
              <div class="p-2 rounded-lg bg-stone-100 dark:bg-stone-800">
                <Bot
                  :size="16"
                  class="text-stone-500"
                />
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">
                  {{ agent.name }}
                </div>
                <div class="text-xs text-stone-400 truncate">
                  {{ agent.model }}
                </div>
              </div>
              <div
                v-if="selectedAgent?.id === agent.id"
                class="text-blue-500"
              >
                <svg
                  class="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
