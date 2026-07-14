<script setup lang="ts">
import { Save, Loader2 } from '@lucide/vue'

const api = useApi()
const loading = ref(true)
const saving = ref(false)
const toast = ref<{ type: 'success' | 'error', message: string } | null>(null)

const prefs = reactive({
  email_notifications: true,
  in_app_notifications: true,
  agent_alerts: true,
  weekly_digest: false,
  security_alerts: true
})

const notifications = [
  { key: 'email_notifications', label: 'Email Notifications', description: 'Receive updates via email' },
  { key: 'in_app_notifications', label: 'In-App Notifications', description: 'Show notifications in the app' },
  { key: 'agent_alerts', label: 'Agent Alerts', description: 'Get notified about agent activity' },
  { key: 'weekly_digest', label: 'Weekly Digest', description: 'Receive a weekly summary email' },
  { key: 'security_alerts', label: 'Security Alerts', description: 'Important security notifications' }
]

async function loadNotifications() {
  loading.value = true
  try {
    const data = await api.settings.getNotifications()
    Object.assign(prefs, data)
  } catch {
    toast.value = { type: 'error', message: 'Failed to load notification preferences' }
  } finally {
    loading.value = false
  }
}

async function saveNotifications() {
  saving.value = true
  try {
    await api.settings.updateNotifications({ ...prefs })
    toast.value = { type: 'success', message: 'Notification preferences saved' }
  } catch {
    toast.value = { type: 'error', message: 'Failed to save notification preferences' }
  } finally {
    saving.value = false
  }
}

onMounted(loadNotifications)
</script>

<template>
  <UCard>
    <div
      v-if="loading"
      class="flex justify-center py-8"
    >
      <Loader2 class="w-6 h-6 animate-spin text-muted" />
    </div>
    <div
      v-else
      class="space-y-6"
    >
      <div
        v-for="n in notifications"
        :key="n.key"
        class="flex items-center justify-between p-4 border rounded-lg"
      >
        <div>
          <div class="font-medium">
            {{ n.label }}
          </div>
          <div class="text-sm text-muted">
            {{ n.description }}
          </div>
        </div>
        <USwitch v-model="(prefs as any)[n.key]" />
      </div>
      <div class="flex justify-end">
        <UButton
          :loading="saving"
          @click="saveNotifications"
        >
          <Save class="w-4 h-4 mr-2" />
          Save Preferences
        </UButton>
      </div>
    </div>
    <div
      v-if="toast"
      :class="['fixed bottom-4 right-4 p-4 rounded-lg shadow-lg z-50', toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white']"
    >
      {{ toast.message }}
    </div>
  </UCard>
</template>
