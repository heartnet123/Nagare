<script setup lang="ts">
import {
  Waves,
  Search,
  BarChart2,
  CheckCircle2,
  Activity,
  Sparkles,
  Bot,
  ArrowRight
} from '@lucide/vue'

definePageMeta({
  layout: 'default'
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-6 pb-12 hide-scrollbar flex items-center justify-center">
    <div class="max-w-3xl mx-auto w-full">
      <!-- Hero -->
      <div class="flex flex-col items-center justify-center mb-8">
        <div class="text-blue-600 mb-6">
          <Waves
            :size="56"
            :stroke-width="1.5"
          />
        </div>
        <h1 class="text-4xl md:text-5xl font-semibold tracking-tight mb-3 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
          Good morning
        </h1>
        <p class="text-lg md:text-xl text-stone-500 font-medium">
          How can I help you today?
        </p>
      </div>

      <HomeComposer />

      <!-- Action chips -->
      <div class="flex flex-wrap items-center justify-center gap-3 mb-16">
        <NuxtLink
          to="/knowledge"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 bg-white text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 hover:border-stone-300 shadow-sm transition-all"
        >
          <Search
            :size="16"
            :stroke-width="1.5"
          />
          Search Knowledge
        </NuxtLink>
        <NuxtLink
          to="/analytics"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 bg-white text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 hover:border-stone-300 shadow-sm transition-all"
        >
          <BarChart2
            :size="16"
            :stroke-width="1.5"
          />
          Analyze Data
        </NuxtLink>
        <NuxtLink
          to="/evaluations"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 bg-white text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 hover:border-stone-300 shadow-sm transition-all"
        >
          <CheckCircle2
            :size="16"
            :stroke-width="1.5"
          />
          Evaluate Response
        </NuxtLink>
        <NuxtLink
          to="/monitoring"
          class="flex items-center gap-2 px-4 py-2 rounded-full border border-stone-200 bg-white text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-50 hover:border-stone-300 shadow-sm transition-all"
        >
          <Activity
            :size="16"
            :stroke-width="1.5"
          />
          System Status
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
