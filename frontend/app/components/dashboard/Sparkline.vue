<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    data: number[]
    color?: string
  }>(),
  {
    color: '#3b82f6'
  }
)

const height = 24
const width = 100

const points = computed(() => {
  if (!props.data || props.data.length === 0) return ''
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  return props.data
    .map((val, i) => {
      const x = (i / (props.data.length - 1)) * width
      const y = height - ((val - min) / range) * height
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<template>
  <svg
    class="w-full h-full"
    preserveAspectRatio="none"
    :viewBox="`0 0 ${width} ${height}`"
    aria-hidden="true"
  >
    <polyline
      fill="none"
      :stroke="color"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      :points="points"
    />
  </svg>
</template>
