<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

interface UsageStats {
  model_id: string
  model_name: string
  total_input_tokens: number
  total_output_tokens: number
  total_cost: number
  request_count: number
  last_used: string | null
}

interface UsageSummary {
  models: UsageStats[]
  total_input_tokens: number
  total_output_tokens: number
  total_cost: number
}

defineProps<{
  summary: UsageSummary | null
  loading: boolean
}>()

const columns: TableColumn<UsageStats>[] = [
  { id: 'model_name', header: 'Model', accessorKey: 'model_name' },
  { id: 'total_input_tokens', header: 'Input Tokens', accessorKey: 'total_input_tokens' },
  { id: 'total_output_tokens', header: 'Output Tokens', accessorKey: 'total_output_tokens' },
  { id: 'total_cost', header: 'Cost', accessorKey: 'total_cost' },
  { id: 'request_count', header: 'Requests', accessorKey: 'request_count' }
]

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return n.toLocaleString()
}

function formatCost(cost: number): string {
  return `$${cost.toFixed(4)}`
}
</script>

<template>
  <div class="space-y-6">
    <div
      v-if="loading"
      class="grid grid-cols-1 md:grid-cols-3 gap-4"
    >
      <USkeleton class="h-24" />
      <USkeleton class="h-24" />
      <USkeleton class="h-24" />
    </div>

    <template v-else-if="summary">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UCard>
          <div class="text-sm text-muted">
            Total Input Tokens
          </div>
          <div class="text-2xl font-bold">
            {{ formatNumber(summary.total_input_tokens) }}
          </div>
        </UCard>
        <UCard>
          <div class="text-sm text-muted">
            Total Output Tokens
          </div>
          <div class="text-2xl font-bold">
            {{ formatNumber(summary.total_output_tokens) }}
          </div>
        </UCard>
        <UCard>
          <div class="text-sm text-muted">
            Total Cost
          </div>
          <div class="text-2xl font-bold text-primary">
            {{ formatCost(summary.total_cost) }}
          </div>
        </UCard>
      </div>

      <UCard v-if="summary.models.length > 0">
        <template #header>
          <h3 class="text-lg font-semibold">
            Per-Model Breakdown
          </h3>
        </template>
        <UTable
          :data="summary.models"
          :columns="columns"
        >
          <template #total_input_tokens-cell="{ row }">
            {{ formatNumber(row.original.total_input_tokens) }}
          </template>
          <template #total_output_tokens-cell="{ row }">
            {{ formatNumber(row.original.total_output_tokens) }}
          </template>
          <template #total_cost-cell="{ row }">
            {{ formatCost(row.original.total_cost) }}
          </template>
        </UTable>
      </UCard>

      <UCard v-else>
        <div class="text-center text-muted py-8">
          No usage data recorded yet.
        </div>
      </UCard>
    </template>
  </div>
</template>
