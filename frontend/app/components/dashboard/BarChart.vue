<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    data: number[]
    labels?: string[]
    color?: string
    height?: number
    label?: string
    ariaLabel?: string
  }>(),
  {
    color: '#00C16A',
    height: 160
  }
)

const max = computed(() => Math.max(...props.data) || 1)
</script>

<template>
  <div class="relative w-full">
    <!-- Accessible Summary Table (screen reader only) -->
    <div class="sr-only">
      <table class="w-full text-xs">
        <caption>{{ label || 'Bar Chart' }}</caption>
        <thead>
          <tr>
            <th scope="col">
              Data Point
            </th>
            <th scope="col">
              Value
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(v, i) in data"
            :key="i"
          >
            <td>{{ labels && labels[i] ? labels[i] : `Point ${i + 1}` }}</td>
            <td>{{ v }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div
      class="flex items-end gap-2"
      :style="{ height: `${height}px` }"
      role="img"
      :aria-label="ariaLabel || label || 'Bar Chart showing data'"
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
          class="text-[10px] text-stone-400 dark:text-stone-500"
        >
          {{ labels[i] }}
        </span>
      </div>
    </div>
  </div>
</template>
