<script setup lang="ts">
import { Search, Plus } from '@lucide/vue'
import type { Connection } from '~/types/connection'
import ConnectionCard from './ConnectionCard.vue'

defineProps<{
  connections: Connection[]
  categories: readonly string[]
  activeFilter: string
  searchQuery: string
  selectedConnectionId: string
  detailPanelOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery' | 'update:activeFilter', val: string): void
  (e: 'selectConnection', conn: Connection): void
  (e: 'openDetailPanel'): void
}>()
</script>

<template>
  <div>
    <!-- Page Header Row -->
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-7">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-default">
          Connections
        </h1>
        <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Bring your tools, data, and workflows into one system.
        </p>
      </div>
      <div class="text-left sm:text-right shrink-0">
        <p class="text-xs font-semibold text-slate-800 dark:text-slate-100">
          Mon, Apr 28, 2025
        </p>
        <p class="text-[11px] text-slate-400 mt-0.5">
          A calmer, more productive day.
        </p>
      </div>
    </div>

    <!-- Search & Add Bar -->
    <div class="flex items-center gap-3 mb-6">
      <div class="relative flex-1">
        <Search
          :size="16"
          class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
        />
        <input
          :value="searchQuery"
          type="text"
          placeholder="Search integrations..."
          class="w-full pl-10 pr-4 py-2 text-xs sm:text-sm bg-white dark:bg-elevated border border-slate-200/90 dark:border-slate-700 rounded-xl placeholder-slate-400 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-xs"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-if="!detailPanelOpen"
          type="button"
          class="px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs sm:text-sm font-semibold transition-colors shrink-0"
          @click="emit('openDetailPanel')"
        >
          Details
        </button>
        <button
          type="button"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs sm:text-sm font-semibold shadow-sm transition-colors shrink-0"
        >
          <Plus
            :size="16"
            :stroke-width="2.5"
          />
          <span>Add connection</span>
        </button>
      </div>
    </div>

    <!-- Filter Pills & Result Count -->
    <div class="flex items-center justify-between gap-4 mb-6 overflow-x-auto pb-1">
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          class="px-3.5 py-1 rounded-full text-xs font-medium transition-colors"
          :class="[
            activeFilter === cat
              ? 'bg-blue-600 text-white shadow-xs'
              : 'bg-slate-100 dark:bg-muted hover:bg-slate-200/80 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300'
          ]"
          @click="emit('update:activeFilter', cat)"
        >
          {{ cat }}
        </button>
      </div>
      <span class="text-xs text-slate-400 font-medium shrink-0">
        {{ connections.length }} results
      </span>
    </div>

    <!-- 3-Column Integration Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5">
      <ConnectionCard
        v-for="conn in connections"
        :key="conn.id"
        :connection="conn"
        :is-selected="selectedConnectionId === conn.id && detailPanelOpen"
        @select="emit('selectConnection', $event)"
      />
    </div>
  </div>
</template>
