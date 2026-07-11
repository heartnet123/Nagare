<script setup lang="ts">
const api = useApi()
const config = ref<Record<string, unknown> | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function fetchConfig() {
  loading.value = true
  error.value = null
  try {
    config.value = await api.models.config()
  } catch (e) {
    const err = e as { data?: { message?: string }, message?: string }
    error.value = err?.data?.message ?? err?.message ?? 'Failed to load configuration'
  } finally {
    loading.value = false
  }
}

onMounted(fetchConfig)

function maskApiKey(key: string | undefined): string {
  if (!key) return 'Not set'
  if (key.length <= 8) return '••••••••'
  return key.slice(0, 4) + '••••' + key.slice(-4)
}
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">
          Model Configuration
        </h3>
        <UButton
          variant="soft"
          size="sm"
          @click="fetchConfig"
        >
          Refresh
        </UButton>
      </div>
    </template>

    <div
      v-if="loading"
      class="space-y-4"
    >
      <USkeleton class="h-12" />
      <USkeleton class="h-12" />
      <USkeleton class="h-12" />
    </div>

    <div v-else-if="error">
      <UAlert
        :title="error"
        color="error"
      />
    </div>

    <div
      v-else-if="config"
      class="space-y-4"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="space-y-1">
          <div class="text-sm text-muted">
            Default Model
          </div>
          <div class="font-mono text-sm">
            {{ config.default_model || 'Not configured' }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-sm text-muted">
            API Base URL
          </div>
          <div class="font-mono text-sm">
            {{ config.base_url || 'Not configured' }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-sm text-muted">
            API Key
          </div>
          <div class="font-mono text-sm">
            {{ maskApiKey(config.api_key as string) }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-sm text-muted">
            Provider
          </div>
          <div class="font-mono text-sm">
            {{ config.provider || 'Auto-detect' }}
          </div>
        </div>
      </div>
    </div>

    <div
      v-else
      class="text-center text-muted py-8"
    >
      No configuration available.
    </div>
  </UCard>
</template>
