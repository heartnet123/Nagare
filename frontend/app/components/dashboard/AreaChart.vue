<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    data: number[]
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

const width = 320
const pad = 8

const chartData = computed(() => {
  if (!props.data || props.data.length === 0) {
    return { line: '', area: '', gid: 'area-default' }
  }
  const max = Math.max(...props.data)
  const min = Math.min(...props.data)
  const range = max - min || 1
  const stepX = (width - pad * 2) / (props.data.length - 1)

  const pts = props.data.map((v, i) => {
    const x = pad + i * stepX
    const y = pad + (1 - (v - min) / range) * (props.height - pad * 2)
    return [x, y]
  })

  const line = pts.map(([x, y]) => `${x},${y}`).join(' ')
  const area = `${pad},${props.height - pad} ${line} ${width - pad},${props.height - pad}`
  const gid = `area-${props.color.replace('#', '')}`

  return { line, area, gid }
})
</script>

<template>
  <div class="relative w-full">
    <!-- Accessible Summary Table (screen reader only) -->
    <div class="sr-only">
      <table class="w-full text-xs">
        <caption>{{ label || 'Area Chart' }}</caption>
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
            <td>Point {{ i + 1 }}</td>
            <td>{{ v }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <svg
      :viewBox="`0 0 ${width} ${height}`"
      class="w-full"
      preserveAspectRatio="none"
      role="img"
      :aria-label="ariaLabel || label || 'Area Chart showing data trend'"
    >
      <defs>
        <linearGradient
          :id="chartData.gid"
          x1="0"
          y1="0"
          x2="0"
          y2="1"
        >
          <stop
            offset="0%"
            :stop-color="color"
            stop-opacity="0.18"
          />
          <stop
            offset="100%"
            :stop-color="color"
            stop-opacity="0"
          />
        </linearGradient>
      </defs>
      <polygon
        :points="chartData.area"
        :fill="`url(#${chartData.gid})`"
      />
      <polyline
        :points="chartData.line"
        fill="none"
        :stroke="color"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </div>
</template>
