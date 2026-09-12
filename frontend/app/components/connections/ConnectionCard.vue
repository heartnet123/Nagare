<script setup lang="ts">
import { MoreHorizontal } from '@lucide/vue'
import type { Connection } from '~/types/connection'
import ConnectionIcon from './ConnectionIcon.vue'

defineProps<{
  connection: Connection
  isSelected: boolean
}>()

const emit = defineEmits<{
  (e: 'select', conn: Connection): void
}>()
</script>

<template>
  <div
    class="bg-white dark:bg-stone-900 rounded-2xl border transition-all p-5 flex flex-col justify-between cursor-pointer"
    :class="[
      isSelected
        ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-xs'
        : 'border-stone-200 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700 hover:shadow-xs'
    ]"
    @click="emit('select', connection)"
  >
    <div>
      <!-- Top Row: Icon, Title, Status & Options -->
      <div class="flex items-start justify-between gap-2 mb-2">
        <div class="flex items-start gap-3 min-w-0">
          <div class="w-10 h-10 rounded-xl bg-stone-50 dark:bg-stone-800 border border-stone-100 dark:border-stone-700/60 flex items-center justify-center shrink-0 p-2 text-stone-700 dark:text-stone-200">
            <ConnectionIcon :name="connection.id" />
          </div>

          <div class="min-w-0">
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100 leading-tight truncate">
              {{ connection.name }}
            </h3>
            <p class="text-[11px] text-stone-500 dark:text-stone-400 mt-1 leading-normal line-clamp-2">
              {{ connection.description }}
            </p>
          </div>
        </div>

        <!-- Status Pill & Options -->
        <div class="flex items-center gap-1.5 shrink-0">
          <span
            v-if="connection.status === 'connected'"
            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400" />
            Connected
          </span>
          <span
            v-else
            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 dark:bg-blue-400" />
            Available
          </span>

          <button
            v-if="connection.status === 'connected'"
            type="button"
            class="p-1 text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 rounded-md hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
            @click.stop
          >
            <MoreHorizontal :size="15" />
          </button>
        </div>
      </div>

      <!-- Metadata Rows -->
      <div class="space-y-1.5 mt-4 pt-3 border-t border-stone-100 dark:border-stone-800">
        <div class="flex items-start justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500 w-24 shrink-0">Last sync</span>
          <span class="text-stone-700 dark:text-stone-200 font-medium text-right truncate">{{ connection.lastSync }}</span>
        </div>
        <div class="flex items-start justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500 w-24 shrink-0">Permissions</span>
          <span class="text-stone-700 dark:text-stone-200 font-medium text-right truncate">{{ connection.permissions }}</span>
        </div>
        <div class="flex items-start justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500 w-24 shrink-0">Data types</span>
          <span class="text-stone-700 dark:text-stone-200 font-medium text-right truncate">{{ connection.dataTypes }}</span>
        </div>
      </div>
    </div>

    <!-- Action Button -->
    <div class="mt-5 pt-2">
      <button
        v-if="connection.status === 'connected'"
        type="button"
        class="w-full py-2 px-3 rounded-xl border border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-800 hover:bg-stone-50 dark:hover:bg-stone-700 text-stone-700 dark:text-stone-200 text-xs font-semibold text-center transition-colors shadow-xs"
        @click.stop="emit('select', connection)"
      >
        Configure
      </button>
      <button
        v-else
        type="button"
        class="w-full py-2 px-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold text-center shadow-xs transition-colors"
        @click.stop="emit('select', connection)"
      >
        Connect
      </button>
    </div>
  </div>
</template>
