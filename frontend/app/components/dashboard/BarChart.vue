<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    data: number[]
    labels?: string[]
    color?: string
    height?: number
  }>(),
  {
    color: '#3b82f6',
    height: 160
  }
)

const max = computed(() => Math.max(...props.data) || 1)
</script>

<template>
  <div
    class="flex items-end gap-2"
    :style="{ height: `${height}px` }"
  >
    <div
      v-for="(v, i) in data"
      :key="i"
      class="flex-1 flex flex-col items-center justify-end gap-2 h-full"
    >
      <div
        class="w-full rounded-t-md transition-all"
        :style="{
          height: `${(v / max) * 100}%`,
          backgroundColor: color,
          opacity: 0.85
        }"
      />
      <span
        v-if="labels && labels[i]"
        class="text-[10px] text-stone-400"
      >
        {{ labels[i] }}
      </span>
    </div>
  </div>
</template>
