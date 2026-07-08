<script setup lang="ts">
import { BookOpen } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const features = [
  'Upload files or connect data sources',
  'Configurable chunking and embedding',
  'Index health and freshness monitoring',
  'Full-text and semantic search preview'
]
</script>

<template>
  <DashboardSectionPlaceholder
    :icon="BookOpen"
    title="Knowledge"
    description="Your connected sources of truth. Ingest, chunk, and index documents for retrieval."
    :features="features"
  />
</template>
