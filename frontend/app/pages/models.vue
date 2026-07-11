<script setup lang="ts">
import { Box, BarChart3, Settings } from '@lucide/vue'
import type { RegistryModel, UsageSummary } from '~/composables/useApi/models'

definePageMeta({ layout: 'default' })

const api = useApi()
const models = ref<RegistryModel[]>([])
const usageSummary = ref<UsageSummary | null>(null)
const loading = ref(true)
const activeTab = ref('models')

const tabs = [
  { slot: 'models', label: 'Models', icon: Box },
  { slot: 'usage', label: 'Usage Stats', icon: BarChart3 },
  { slot: 'config', label: 'Configuration', icon: Settings }
]

async function fetchModels() {
  try {
    models.value = await api.models.list()
  } catch (e) {
    console.error('Failed to load models:', e)
  }
}

async function fetchUsageSummary() {
  try {
    usageSummary.value = await api.models.usageSummary()
  } catch (e) {
    console.error('Failed to load usage stats:', e)
  }
}

onMounted(async () => {
  loading.value = true
  await Promise.all([fetchModels(), fetchUsageSummary()])
  loading.value = false
})
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Models Registry
        </h1>
        <p class="text-muted">
          Manage language models, track usage, and monitor costs.
        </p>
      </div>
    </div>

    <UTabs
      v-model="activeTab"
      :items="tabs"
    >
      <template #models>
        <ModelTable
          :models="models"
          :loading="loading"
        />
      </template>
      <template #usage>
        <UsageStats
          :summary="usageSummary"
          :loading="loading"
        />
      </template>
      <template #config>
        <ConfigViewer />
      </template>
    </UTabs>
  </div>
</template>
