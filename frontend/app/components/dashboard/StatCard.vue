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
  <div class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <div class="p-2 rounded-lg bg-stone-50 text-stone-500">
        <component
          :is="icon"
          :size="18"
          :stroke-width="1.5"
        />
      </div>
      <span
        v-if="trend"
        class="text-xs font-semibold"
        :class="trendPositive !== false ? 'text-emerald-600' : 'text-red-500'"
      >
        {{ trend }}
      </span>
    </div>
    <span class="text-2xl font-semibold text-stone-900 leading-none">{{ value }}</span>
    <span class="mt-1.5 text-xs text-stone-500 font-medium">{{ label }}</span>
  </div>
</template>
