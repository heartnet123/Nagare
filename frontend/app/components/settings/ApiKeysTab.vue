<script setup lang="ts">
import { Plus, Trash2, Ban, Copy, Check, Loader2 } from '@lucide/vue'
import type { ApiKey } from '~/composables/useApi/settings'

const api = useApi()
const loading = ref(true)
const keys = ref<ApiKey[]>([])
const toast = ref<{ type: 'success' | 'error', message: string } | null>(null)

// Create modal state
const showCreateModal = ref(false)
const creating = ref(false)
const newKey = reactive({
  name: '',
  description: '',
  expires_at: ''
})

// Created key display
const createdKey = ref<string | null>(null)
const showCreatedModal = computed({
  get: () => !!createdKey.value,
  set: (val) => {
    if (!val) createdKey.value = null
  }
})
const copied = ref(false)

// Delete confirmation
const showDeleteModal = ref(false)
const keyToDelete = ref<string | null>(null)
const deleting = ref(false)

async function loadKeys() {
  loading.value = true
  try {
    keys.value = await api.settings.listApiKeys()
  } catch {
    toast.value = { type: 'error', message: 'Failed to load API keys' }
  } finally {
    loading.value = false
  }
}

async function createKey() {
  creating.value = true
  try {
    const result = await api.settings.createApiKey({
      name: newKey.name,
      description: newKey.description || undefined,
      expires_at: newKey.expires_at || undefined
    })
    createdKey.value = result.key || null
    showCreateModal.value = false
    newKey.name = ''
    newKey.description = ''
    newKey.expires_at = ''
    await loadKeys()
    toast.value = { type: 'success', message: 'API key created' }
  } catch {
    toast.value = { type: 'error', message: 'Failed to create API key' }
  } finally {
    creating.value = false
  }
}

async function revokeKey(id: string) {
  try {
    await api.settings.revokeApiKey(id)
    await loadKeys()
    toast.value = { type: 'success', message: 'API key revoked' }
  } catch {
    toast.value = { type: 'error', message: 'Failed to revoke API key' }
  }
}

function confirmDelete(id: string) {
  keyToDelete.value = id
  showDeleteModal.value = true
}

async function deleteKey() {
  if (!keyToDelete.value) return
  deleting.value = true
  try {
    await api.settings.deleteApiKey(keyToDelete.value)
    showDeleteModal.value = false
    keyToDelete.value = null
    await loadKeys()
    toast.value = { type: 'success', message: 'API key deleted' }
  } catch {
    toast.value = { type: 'error', message: 'Failed to delete API key' }
  } finally {
    deleting.value = false
  }
}

async function copyKey() {
  if (!createdKey.value) return
  try {
    await navigator.clipboard.writeText(createdKey.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    toast.value = { type: 'error', message: 'Failed to copy key' }
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadKeys)
</script>

<template>
  <UCard>
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold">
        API Keys
      </h3>
      <UButton @click="showCreateModal = true">
        <Plus class="w-4 h-4 mr-2" />
        Create API Key
      </UButton>
    </div>

    <div
      v-if="loading"
      class="flex justify-center py-8"
    >
      <Loader2 class="w-6 h-6 animate-spin text-muted" />
    </div>

    <div
      v-else-if="keys.length === 0"
      class="text-center py-8 text-muted"
    >
      No API keys yet. Create one to get started.
    </div>

    <div
      v-else
      class="space-y-3"
    >
      <div
        v-for="key in keys"
        :key="key.id"
        class="flex items-center justify-between p-4 border rounded-lg"
      >
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ key.name }}</span>
            <span
              v-if="!key.is_active"
              class="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded"
            >Revoked</span>
          </div>
          <div class="text-sm text-muted mt-1">
            <code class="bg-muted px-1 rounded">{{ key.key_prefix }}...</code>
            <span class="ml-2">Created {{ formatDate(key.created_at) }}</span>
            <span
              v-if="key.last_used_at"
              class="ml-2"
            >Last used {{ formatDate(key.last_used_at) }}</span>
          </div>
          <div
            v-if="key.description"
            class="text-sm text-muted mt-1"
          >
            {{ key.description }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <UButton
            v-if="key.is_active"
            variant="ghost"
            color="warning"
            @click="revokeKey(key.id)"
          >
            <Ban class="w-4 h-4" />
          </UButton>
          <UButton
            variant="ghost"
            color="error"
            @click="confirmDelete(key.id)"
          >
            <Trash2 class="w-4 h-4" />
          </UButton>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <UModal v-model:open="showCreateModal">
      <template #header>
        <h3 class="text-lg font-semibold">
          Create API Key
        </h3>
      </template>
      <template #body>
        <form
          class="space-y-4"
          @submit.prevent="createKey"
        >
          <UFormGroup
            label="Name"
            required
          >
            <UInput
              v-model="newKey.name"
              placeholder="My API Key"
            />
          </UFormGroup>
          <UFormGroup label="Description">
            <UInput
              v-model="newKey.description"
              placeholder="Optional description"
            />
          </UFormGroup>
          <UFormGroup label="Expires At">
            <UInput
              v-model="newKey.expires_at"
              type="date"
            />
          </UFormGroup>
        </form>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            @click="showCreateModal = false"
          >
            Cancel
          </UButton>
          <UButton
            :loading="creating"
            @click="createKey"
          >
            Create
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Created Key Display Modal -->
    <UModal v-model:open="showCreatedModal">
      <template #header>
        <h3 class="text-lg font-semibold">
          API Key Created
        </h3>
      </template>
      <template #body>
        <div class="space-y-4">
          <p class="text-sm text-muted">
            Copy this key now. You won't be able to see it again.
          </p>
          <div class="flex items-center gap-2 p-3 bg-muted rounded-lg">
            <code class="flex-1 text-sm break-all">{{ createdKey }}</code>
            <UButton
              variant="ghost"
              size="sm"
              @click="copyKey"
            >
              <Check
                v-if="copied"
                class="w-4 h-4 text-green-500"
              />
              <Copy
                v-else
                class="w-4 h-4"
              />
            </UButton>
          </div>
        </div>
      </template>
      <template #footer>
        <UButton @click="createdKey = null">
          Done
        </UButton>
      </template>
    </UModal>

    <!-- Delete Confirmation Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #header>
        <h3 class="text-lg font-semibold">
          Delete API Key
        </h3>
      </template>
      <template #body>
        <p>Are you sure you want to permanently delete this API key? This action cannot be undone.</p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            variant="ghost"
            @click="showDeleteModal = false"
          >
            Cancel
          </UButton>
          <UButton
            color="error"
            :loading="deleting"
            @click="deleteKey"
          >
            Delete
          </UButton>
        </div>
      </template>
    </UModal>

    <div
      v-if="toast"
      :class="['fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50', toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white']"
    >
      {{ toast.message }}
    </div>
  </UCard>
</template>
