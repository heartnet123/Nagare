<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  label: string
  value: string
  trend?: string
  trendPositive?: boolean
}>()
</script>

<template>
  <div class="flex flex-col p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <div class="p-2 rounded-lg bg-stone-50 dark:bg-stone-800 text-stone-500 dark:text-stone-400">
        <component
          :is="icon"
          :size="18"
          :stroke-width="1.5"
        />
      </div>
      <span
        v-if="trend"
        class="text-xs font-semibold"
        :class="trendPositive !== false ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'"
      >
        {{ trend }}
      </span>
    </div>
    <span class="text-2xl font-semibold text-stone-900 dark:text-stone-100 leading-none">{{ value }}</span>
    <span class="mt-1.5 text-xs text-stone-500 dark:text-stone-400 font-medium">{{ label }}</span>
  </div>
</template>
