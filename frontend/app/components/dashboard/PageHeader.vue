<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="flex items-start justify-between gap-4 mt-8 mb-8">
    <div>
      <h1 class="text-2xl md:text-3xl font-semibold tracking-tight text-stone-900 text-balance">
        {{ title }}
      </h1>
      <p
        v-if="description"
        class="mt-1.5 text-sm text-stone-500 leading-relaxed max-w-2xl text-pretty"
      >
        {{ description }}
      </p>
    </div>
    <div
      v-if="$slots.action"
      class="shrink-0"
    >
      <slot name="action" />
    </div>
  </div>
</template>
