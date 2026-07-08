<script setup lang="ts">
import { Workflow } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const features = [
  'Visual drag-and-drop pipeline builder',
  'Configurable retriever, reranker, and generator nodes',
  'Per-stage caching and timeout controls',
  'Versioned pipeline deployments'
]
</script>

<template>
  <DashboardSectionPlaceholder
    :icon="Workflow"
    title="Pipeline"
    description="Design and orchestrate the stages of your retrieval-augmented generation flow."
    :features="features"
  />
</template>
