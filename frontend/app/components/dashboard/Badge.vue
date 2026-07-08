<script setup lang="ts">
withDefaults(
  defineProps<{
    tone?: 'neutral' | 'emerald' | 'blue' | 'amber' | 'red' | 'purple'
  }>(),
  {
    tone: 'neutral'
  }
)

const tones: Record<string, string> = {
  neutral: 'bg-stone-100 text-stone-600 border-stone-200',
  emerald: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  blue: 'bg-blue-50 text-blue-700 border-blue-100',
  amber: 'bg-amber-50 text-amber-700 border-amber-100',
  red: 'bg-red-50 text-red-600 border-red-100',
  purple: 'bg-purple-50 text-purple-700 border-purple-100'
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[11px] font-medium"
    :class="tones[tone]"
  >
    <slot />
  </span>
</template>
