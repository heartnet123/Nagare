<script setup lang="ts">
import { Save, Loader2 } from '@lucide/vue'

const api = useApi()
const loading = ref(true)
const saving = ref(false)
const toast = ref<{ type: 'success' | 'error', message: string } | null>(null)

const form = reactive({
  username: '',
  display_name: '',
  avatar_url: '',
  bio: '',
  email: ''
})

async function loadProfile() {
  loading.value = true
  try {
    const profile = await api.settings.getProfile()
    form.username = profile.username ?? ''
    form.display_name = profile.display_name ?? ''
    form.avatar_url = profile.avatar_url ?? ''
    form.bio = profile.bio ?? ''
    form.email = profile.email ?? ''
  } catch {
    toast.value = { type: 'error', message: 'Failed to load profile' }
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await api.settings.updateProfile({
      username: form.username,
      display_name: form.display_name || null,
      avatar_url: form.avatar_url || null,
      bio: form.bio || null,
      email: form.email || null
    })
    toast.value = { type: 'success', message: 'Profile saved' }
  } catch {
    toast.value = { type: 'error', message: 'Failed to save profile' }
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <UCard>
    <div
      v-if="loading"
      class="flex justify-center py-8"
    >
      <Loader2 class="w-6 h-6 animate-spin text-muted" />
    </div>
    <form
      v-else
      class="space-y-4"
      @submit.prevent="saveProfile"
    >
      <UFormGroup label="Username">
        <UInput
          v-model="form.username"
          placeholder="Username"
        />
      </UFormGroup>
      <UFormGroup label="Display Name">
        <UInput
          v-model="form.display_name"
          placeholder="Display name"
        />
      </UFormGroup>
      <UFormGroup label="Email">
        <UInput
          v-model="form.email"
          type="email"
          placeholder="Email"
        />
      </UFormGroup>
      <UFormGroup label="Avatar URL">
        <UInput
          v-model="form.avatar_url"
          placeholder="https://..."
        />
      </UFormGroup>
      <UFormGroup label="Bio">
        <UInput
          v-model="form.bio"
          placeholder="Tell us about yourself"
        />
      </UFormGroup>
      <div class="flex justify-end">
        <UButton
          type="submit"
          :loading="saving"
        >
          <Save class="w-4 h-4 mr-2" />
          Save Profile
        </UButton>
      </div>
    </form>
    <div
      v-if="toast"
      :class="['fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50', toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white']"
    >
      {{ toast.message }}
    </div>
  </UCard>
</template>
