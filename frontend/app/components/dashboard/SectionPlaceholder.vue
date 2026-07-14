<script setup lang="ts">
import type { Component } from 'vue'
import { ArrowLeft } from '@lucide/vue'

defineProps<{
  icon: Component
  title: string
  description: string
  features: string[]
}>()
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      :title="title"
      :description="description"
    />

    <div class="flex flex-col items-center text-center py-16 px-6 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm">
      <div class="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 mb-5">
        <component
          :is="icon"
          :size="32"
          :stroke-width="1.5"
        />
      </div>
      <h2 class="text-lg font-semibold text-stone-900 dark:text-stone-100 mb-2">
        Coming soon
      </h2>
      <p class="text-sm text-stone-500 dark:text-stone-400 max-w-md mb-8 leading-relaxed text-pretty">
        This module is on the roadmap. Here's what it will include:
      </p>
      <ul class="grid gap-2.5 text-left mb-8 w-full max-w-sm">
        <li
          v-for="f in features"
          :key="f"
          class="flex items-start gap-2.5 text-sm text-stone-600 dark:text-stone-400"
        >
          <span class="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
          {{ f }}
        </li>
      </ul>
      <NuxtLink
        to="/"
        class="flex items-center gap-2 px-4 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 hover:bg-stone-50 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300 text-sm font-medium shadow-sm transition-colors"
      >
        <ArrowLeft
          :size="16"
          :stroke-width="1.5"
        />
        Back to Home
      </NuxtLink>
    </div>
  </DashboardPageScroll>
</template>
