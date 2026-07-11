<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'

interface Model {
  id: string
  name: string
  provider: string
  description: string | null
  input_cost_per_1m: number
  output_cost_per_1m: number
  max_context_length: number
  is_active: boolean
}

defineProps<{
  models: Model[]
  loading: boolean
}>()

const columns: TableColumn<Model>[] = [
  { id: 'name', header: 'Model', accessorKey: 'name' },
  { id: 'provider', header: 'Provider', accessorKey: 'provider' },
  { id: 'input_cost_per_1m', header: 'Input Cost/1M', accessorKey: 'input_cost_per_1m' },
  { id: 'output_cost_per_1m', header: 'Output Cost/1M', accessorKey: 'output_cost_per_1m' },
  { id: 'max_context_length', header: 'Context Length', accessorKey: 'max_context_length' },
  { id: 'is_active', header: 'Status', accessorKey: 'is_active' }
]

function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`
}

function formatTokens(tokens: number): string {
  return tokens.toLocaleString()
}
</script>

<template>
  <UCard>
    <UTable
      :columns="columns"
      :data="models"
      :loading="loading"
    >
      <template #input_cost_per_1m-cell="{ row }">
        {{ formatCost(row.original.input_cost_per_1m) }}
      </template>
      <template #output_cost_per_1m-cell="{ row }">
        {{ formatCost(row.original.output_cost_per_1m) }}
      </template>
      <template #max_context_length-cell="{ row }">
        {{ formatTokens(row.original.max_context_length) }}
      </template>
      <template #is_active-cell="{ row }">
        <UBadge
          :color="row.original.is_active ? 'success' : 'error'"
          variant="soft"
        >
          {{ row.original.is_active ? 'Active' : 'Inactive' }}
        </UBadge>
      </template>
    </UTable>
  </UCard>
</template>
