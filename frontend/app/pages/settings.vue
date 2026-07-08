<script setup lang="ts">
import { Settings } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const features = [
  'Workspace and profile preferences',
  'Team members and role-based access',
  'API keys and webhook management',
  'Billing, usage limits, and plan details'
]
</script>

<template>
  <DashboardSectionPlaceholder
    :icon="Settings"
    title="Settings"
    description="Configure your workspace, team members, billing, and integrations."
    :features="features"
  />
</template>
