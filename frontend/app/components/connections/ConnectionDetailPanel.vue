<script setup lang="ts">
import { ref } from 'vue'
import {
  X,
  CheckCircle2,
  ArrowRight,
  Radio,
  Send,
  User,
  LayoutGrid,
  File
} from '@lucide/vue'
import type { Connection, ConnectionTab } from '~/types/connection'
import ConnectionIcon from './ConnectionIcon.vue'

defineProps<{
  connection: Connection
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggleCapability', capId: string): void
}>()

const activeTab = ref<ConnectionTab>('overview')
</script>

<template>
  <aside class="fixed inset-y-0 right-0 z-30 sm:static sm:z-auto w-full sm:w-[390px] xl:w-[410px] bg-white dark:bg-stone-900 border-l border-stone-200 dark:border-stone-800 flex flex-col shrink-0 h-full overflow-y-auto [scrollbar-width:thin] [scrollbar-color:rgba(120,120,120,0.25)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-stone-300 dark:[&::-webkit-scrollbar-thumb]:bg-stone-700/60 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent shadow-xl sm:shadow-none">
    <!-- Panel Title & Close Button -->
    <div class="px-6 py-4 border-b border-stone-100 dark:border-stone-800 flex items-center justify-between sticky top-0 bg-white/95 dark:bg-stone-900/95 backdrop-blur-sm z-10">
      <h2 class="text-base font-bold text-stone-900 dark:text-stone-100">
        Connection details
      </h2>
      <button
        type="button"
        class="p-1 rounded-md text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
        aria-label="Close panel"
        @click="emit('close')"
      >
        <X :size="18" />
      </button>
    </div>

    <!-- Connection Header Card -->
    <div class="px-6 py-3">
      <div class="flex items-start gap-3.5 mb-2">
        <div class="w-12 h-12 rounded-xl bg-stone-50 dark:bg-stone-800 border border-stone-100 dark:border-stone-700/60 flex items-center justify-center shrink-0 p-2.5 text-stone-700 dark:text-stone-200">
          <ConnectionIcon :name="connection.id" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-base font-bold text-stone-900 dark:text-stone-100 truncate">
              {{ connection.name }}
            </h3>
            <span
              v-if="connection.status === 'connected'"
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40 shrink-0"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400" />
              Connected
            </span>
            <span
              v-else
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800/40 shrink-0"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-blue-500 dark:bg-blue-400" />
              Available
            </span>
          </div>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
            {{ connection.description }}
          </p>
          <p class="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-normal">
            {{ connection.longDescription }}
          </p>
        </div>
      </div>
    </div>

    <!-- Detail Tabs -->
    <div class="flex items-center gap-6 px-6 border-b border-stone-200 dark:border-stone-800 mt-3 text-xs">
      <button
        type="button"
        class="pb-2.5 font-semibold transition-colors relative"
        :class="[activeTab === 'overview' ? 'text-blue-600 dark:text-blue-400' : 'text-stone-500 dark:text-stone-400 hover:text-stone-800 dark:hover:text-stone-200']"
        @click="activeTab = 'overview'"
      >
        Overview
        <span
          v-if="activeTab === 'overview'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'permissions' ? 'text-blue-600 dark:text-blue-400' : 'text-stone-500 dark:text-stone-400 hover:text-stone-800 dark:hover:text-stone-200']"
        @click="activeTab = 'permissions'"
      >
        Permissions
        <span
          v-if="activeTab === 'permissions'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'datatypes' ? 'text-blue-600 dark:text-blue-400' : 'text-stone-500 dark:text-stone-400 hover:text-stone-800 dark:hover:text-stone-200']"
        @click="activeTab = 'datatypes'"
      >
        Data types
        <span
          v-if="activeTab === 'datatypes'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'settings' ? 'text-blue-600 dark:text-blue-400' : 'text-stone-500 dark:text-stone-400 hover:text-stone-800 dark:hover:text-stone-200']"
        @click="activeTab = 'settings'"
      >
        Settings
        <span
          v-if="activeTab === 'settings'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-500 rounded-full"
        />
      </button>
    </div>

    <!-- Tab: Overview -->
    <div
      v-if="activeTab === 'overview'"
      class="px-6 py-5 space-y-6"
    >
      <!-- Key Metadata List -->
      <div class="space-y-2.5">
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Connection status</span>
          <span class="inline-flex items-center gap-1.5 font-semibold text-stone-800 dark:text-stone-200">
            <CheckCircle2
              v-if="connection.status === 'connected'"
              :size="14"
              class="text-emerald-600 dark:text-emerald-400"
            />
            {{ connection.status === 'connected' ? 'Connected' : 'Not configured' }}
          </span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Last sync</span>
          <span class="font-medium text-stone-800 dark:text-stone-200">{{ connection.lastSync }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Connected by</span>
          <span class="font-medium text-stone-800 dark:text-stone-200">{{ connection.connectedBy || '—' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Connected on</span>
          <span class="font-medium text-stone-800 dark:text-stone-200">{{ connection.connectedOn || '—' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Workspace</span>
          <span class="font-medium text-stone-800 dark:text-stone-200">{{ connection.workspace || 'NagareOS' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-stone-400 dark:text-stone-500">Access type</span>
          <span class="font-medium text-stone-800 dark:text-stone-200">{{ connection.accessType || 'OAuth 2.0' }}</span>
        </div>
      </div>

      <!-- Sync History Section -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-xs font-bold text-stone-900 dark:text-stone-100">
            Sync history
          </h4>
          <button
            type="button"
            class="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            <span>View all</span>
            <ArrowRight :size="12" />
          </button>
        </div>

        <div
          v-if="connection.syncHistory.length"
          class="space-y-2.5"
        >
          <div
            v-for="item in connection.syncHistory"
            :key="item.id"
            class="flex items-center justify-between text-xs"
          >
            <div class="flex items-center gap-2 min-w-0">
              <CheckCircle2
                :size="14"
                class="text-emerald-600 dark:text-emerald-400 shrink-0"
              />
              <span class="text-stone-800 dark:text-stone-200 truncate">{{ item.title }}</span>
            </div>
            <span class="text-[11px] text-stone-400 dark:text-stone-500 shrink-0 ml-2">{{ item.time }}</span>
          </div>
        </div>
        <p
          v-else
          class="text-xs text-stone-400 dark:text-stone-500 py-2"
        >
          No sync activity recorded yet.
        </p>
      </div>

      <!-- Enabled Capabilities Section -->
      <div>
        <div class="mb-3">
          <h4 class="text-xs font-bold text-stone-900 dark:text-stone-100">
            Enabled capabilities
          </h4>
          <p class="text-[11px] text-stone-500 dark:text-stone-400 mt-0.5">
            Choose what NagareOS can do with this connection.
          </p>
        </div>

        <div class="space-y-3.5">
          <div
            v-for="cap in connection.capabilities"
            :key="cap.id"
            class="flex items-center justify-between gap-3"
          >
            <div class="flex items-start gap-2.5 min-w-0">
              <div class="w-6 h-6 rounded-md bg-stone-100 dark:bg-stone-800 border border-stone-200/60 dark:border-stone-700/60 flex items-center justify-center text-stone-600 dark:text-stone-300 shrink-0 mt-0.5">
                <Radio
                  v-if="cap.icon === 'target'"
                  :size="13"
                />
                <Send
                  v-else-if="cap.icon === 'send'"
                  :size="13"
                />
                <User
                  v-else-if="cap.icon === 'user'"
                  :size="13"
                />
                <LayoutGrid
                  v-else-if="cap.icon === 'grid'"
                  :size="13"
                />
                <File
                  v-else
                  :size="13"
                />
              </div>
              <div class="min-w-0">
                <p class="text-xs font-semibold text-stone-800 dark:text-stone-200 leading-tight">
                  {{ cap.title }}
                </p>
                <p class="text-[11px] text-stone-400 dark:text-stone-500 mt-0.5 leading-snug truncate">
                  {{ cap.description }}
                </p>
              </div>
            </div>

            <!-- Toggle Switch -->
            <button
              type="button"
              class="w-8 h-4.5 rounded-full transition-colors relative shrink-0 p-0.5 focus:outline-none"
              :class="cap.enabled ? 'bg-blue-600' : 'bg-stone-200 dark:bg-stone-700'"
              :aria-pressed="cap.enabled"
              @click="emit('toggleCapability', cap.id)"
            >
              <span
                class="block w-3.5 h-3.5 rounded-full bg-white transition-transform duration-150 shadow-xs"
                :class="cap.enabled ? 'translate-x-3.5' : 'translate-x-0'"
              />
            </button>
          </div>
        </div>
      </div>

      <!-- Panel Bottom Buttons -->
      <div class="pt-4 border-t border-stone-100 dark:border-stone-800 space-y-2">
        <button
          type="button"
          class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold text-center transition-colors shadow-xs"
        >
          Configure connection
        </button>
        <button
          type="button"
          class="w-full py-1.5 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg text-center transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>

    <!-- Tab: Permissions -->
    <div
      v-else-if="activeTab === 'permissions'"
      class="px-6 py-5 text-xs text-stone-600 dark:text-stone-300 space-y-3"
    >
      <p class="font-semibold text-stone-900 dark:text-stone-100">
        Active Scopes:
      </p>
      <div class="p-3 bg-stone-50 dark:bg-stone-950 rounded-xl border border-stone-200 dark:border-stone-800 font-mono text-[11px] leading-relaxed text-stone-800 dark:text-stone-200">
        {{ connection.permissions }}
      </div>
      <p class="text-stone-400 dark:text-stone-500 text-[11px]">
        Tokens are secured using hardware-backed encryption keys and refreshed automatically.
      </p>
    </div>

    <!-- Tab: Data types -->
    <div
      v-else-if="activeTab === 'datatypes'"
      class="px-6 py-5 text-xs text-stone-600 dark:text-stone-300 space-y-3"
    >
      <p class="font-semibold text-stone-900 dark:text-stone-100">
        Indexed Types:
      </p>
      <div class="p-3 bg-stone-50 dark:bg-stone-950 rounded-xl border border-stone-200 dark:border-stone-800 font-mono text-[11px] leading-relaxed text-stone-800 dark:text-stone-200">
        {{ connection.dataTypes }}
      </div>
    </div>

    <!-- Tab: Settings -->
    <div
      v-else
      class="px-6 py-5 text-xs text-stone-600 dark:text-stone-300 space-y-3"
    >
      <p class="font-semibold text-stone-900 dark:text-stone-100">
        Advanced Settings:
      </p>
      <p class="text-stone-500 dark:text-stone-400 text-xs">
        Webhook event subscription active. Polling fallback interval: 5 minutes.
      </p>
    </div>
  </aside>
</template>
