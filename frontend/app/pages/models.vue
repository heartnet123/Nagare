<script setup lang="ts">
import { Box } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const features = [
  'Connect provider models and API keys',
  'Set default generation and embedding models',
  'Per-model cost and rate-limit controls',
  'A/B routing between model variants'
]
</script>

<template>
  <DashboardSectionPlaceholder
    :icon="Box"
    title="Models"
    description="Manage the language and embedding models available to your workspace."
    :features="features"
  />
</template>
