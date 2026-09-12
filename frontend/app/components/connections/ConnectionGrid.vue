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
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-7">
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900 dark:text-stone-100">
          Connections
        </h1>
        <p class="text-xs sm:text-sm text-stone-500 dark:text-stone-400 mt-1">
          Bring your tools, data, and workflows into one system.
        </p>
      </div>
      <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-stone-50 dark:bg-stone-900 border border-stone-200 dark:border-stone-800 text-xs text-stone-500 dark:text-stone-400 shrink-0">
        <span class="font-medium text-stone-700 dark:text-stone-300">Mon, Apr 28, 2025</span>
        <span class="text-stone-300 dark:text-stone-600">·</span>
        <span>A calmer, more productive day.</span>
      </div>
    </div>

    <!-- Search & Add Bar -->
    <div class="flex items-center gap-3 mb-6">
      <div class="relative flex-1">
        <Search
          :size="16"
          class="absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400 dark:text-stone-500 pointer-events-none"
        />
        <input
          :value="searchQuery"
          type="text"
          placeholder="Search integrations..."
          class="w-full pl-10 pr-4 py-2 text-xs sm:text-sm bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-xl placeholder-stone-400 dark:placeholder-stone-500 text-stone-900 dark:text-stone-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-xs"
          @input="emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          v-if="!detailPanelOpen"
          type="button"
          class="px-3.5 py-2 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 hover:bg-stone-50 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300 text-xs sm:text-sm font-semibold transition-colors shrink-0"
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
              : 'bg-stone-100 hover:bg-stone-200/80 dark:bg-stone-800/80 dark:hover:bg-stone-700 text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 border border-stone-200/60 dark:border-stone-800'
          ]"
          @click="emit('update:activeFilter', cat)"
        >
          {{ cat }}
        </button>
      </div>
      <span class="text-xs text-stone-400 dark:text-stone-500 font-medium shrink-0">
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
