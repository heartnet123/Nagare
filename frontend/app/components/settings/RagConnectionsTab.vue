<script setup lang="ts">
import type { RagConnection } from '~/composables/useApi/settings'

const api = useApiSettings()
const connections = ref<RagConnection[]>([])
const form = reactive({ name: '', base_url: '', model: '', api_key: '' })
const status = ref('')
const loading = ref(false)

async function load() {
  connections.value = await api.listRagConnections()
}
async function test() {
  loading.value = true
  try {
    const res = await api.testRagConnection(form)
    status.value = res.message
  } catch {
    status.value = 'Connection failed'
  } finally {
    loading.value = false
  }
}
async function save() {
  loading.value = true
  try {
    await api.createRagConnection(form)
    status.value = 'Connection saved'
    Object.assign(form, { name: '', base_url: '', model: '', api_key: '' })
    await load()
  } catch {
    status.value = 'Could not save connection'
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <UCard class="mt-6">
    <h3 class="text-lg font-semibold">
      RAG Connections
    </h3>
    <p class="text-sm text-muted mb-4">
      OpenAI-compatible endpoints. API keys stay encrypted on server.
    </p>
    <form
      class="grid gap-4 md:grid-cols-2"
      @submit.prevent="save"
    >
      <UInput
        v-model="form.name"
        placeholder="Name"
        required
      />
      <UInput
        v-model="form.base_url"
        placeholder="https://api.example.com/v1"
        type="url"
        required
      />
      <UInput
        v-model="form.model"
        placeholder="Model"
        required
      />
      <UInput
        v-model="form.api_key"
        placeholder="API key"
        type="password"
        required
      />
      <div class="flex gap-2 md:col-span-2">
        <UButton
          type="button"
          variant="outline"
          :loading="loading"
          @click="test"
        >
          Test connection
        </UButton>
        <UButton
          type="submit"
          :loading="loading"
        >
          Save connection
        </UButton>
        <span
          v-if="status"
          class="self-center text-sm text-muted"
        >{{ status }}</span>
      </div>
    </form>
    <div
      v-if="connections.length"
      class="mt-5 space-y-2"
    >
      <div
        v-for="connection in connections"
        :key="connection.id"
        class="rounded border p-3 text-sm"
      >
        <strong>{{ connection.name }}</strong> · {{ connection.base_url }} · {{ connection.model }} · key stored
      </div>
    </div>
  </UCard>
</template>
