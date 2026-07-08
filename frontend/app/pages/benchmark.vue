<script setup lang="ts">
import { Target } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const features = [
  'Side-by-side configuration comparison',
  'Leaderboard across faithfulness, latency, and cost',
  'Regression detection between versions',
  'Exportable benchmark reports'
]
</script>

<template>
  <DashboardSectionPlaceholder
    :icon="Target"
    title="Benchmark"
    description="Compare model and retriever configurations head-to-head on standardized test suites."
    :features="features"
  />
</template>
