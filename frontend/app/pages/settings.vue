<script setup lang="ts">
import { User, Key, Bell, Palette, Cable } from '@lucide/vue'

definePageMeta({ layout: 'default' })

const activeTab = ref('profile')

const tabs = [
  { slot: 'profile', label: 'Profile', icon: User },
  { slot: 'api-keys', label: 'API Keys', icon: Key },
  { slot: 'rag', label: 'RAG', icon: Cable },
  { slot: 'notifications', label: 'Notifications', icon: Bell },
  { slot: 'theme', label: 'Theme', icon: Palette }
]
</script>

<template>
  <div class="p-6 space-y-6">
    <div>
      <h1 class="text-2xl font-bold">
        Settings
      </h1>
      <p class="text-muted">
        Manage your account, API keys, and preferences.
      </p>
    </div>

    <UTabs
      v-model="activeTab"
      :items="tabs"
    >
      <template #profile>
        <ProfileTab />
      </template>
      <template #api-keys>
        <ApiKeysTab />
      </template>
      <template #rag>
        <RagConnectionsTab />
      </template>
      <template #notifications>
        <NotificationsTab />
      </template>
      <template #theme>
        <ThemeTab />
      </template>
    </UTabs>
  </div>
</template>
