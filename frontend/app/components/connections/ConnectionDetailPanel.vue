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
  <aside class="fixed inset-y-0 right-0 z-30 sm:static sm:z-auto w-full sm:w-[390px] xl:w-[410px] bg-white border-l border-slate-200/90 flex flex-col shrink-0 h-full overflow-y-auto shadow-xl sm:shadow-none">
    <!-- Panel Title & Close Button -->
    <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur-xs z-10">
      <h2 class="text-base font-bold text-slate-900">
        Connection details
      </h2>
      <button
        type="button"
        class="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        aria-label="Close panel"
        @click="emit('close')"
      >
        <X :size="18" />
      </button>
    </div>

    <!-- Connection Header Card -->
    <div class="px-6 py-3">
      <div class="flex items-start gap-3.5 mb-2">
        <div class="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0 p-2.5">
          <ConnectionIcon :name="connection.id" />
        </div>
        <div class="min-w-0 flex-1">
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-base font-bold text-slate-900 truncate">
              {{ connection.name }}
            </h3>
            <span
              v-if="connection.status === 'connected'"
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 shrink-0"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Connected
            </span>
            <span
              v-else
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 text-blue-600 shrink-0"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-blue-500" />
              Available
            </span>
          </div>
          <p class="text-xs text-slate-500 mt-0.5">
            {{ connection.description }}
          </p>
          <p class="text-xs text-slate-500 mt-1 leading-normal">
            {{ connection.longDescription }}
          </p>
        </div>
      </div>
    </div>

    <!-- Detail Tabs -->
    <div class="flex items-center gap-6 px-6 border-b border-slate-200 mt-3 text-xs">
      <button
        type="button"
        class="pb-2.5 font-semibold transition-colors relative"
        :class="[activeTab === 'overview' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800']"
        @click="activeTab = 'overview'"
      >
        Overview
        <span
          v-if="activeTab === 'overview'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'permissions' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800']"
        @click="activeTab = 'permissions'"
      >
        Permissions
        <span
          v-if="activeTab === 'permissions'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'datatypes' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800']"
        @click="activeTab = 'datatypes'"
      >
        Data types
        <span
          v-if="activeTab === 'datatypes'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"
        />
      </button>
      <button
        type="button"
        class="pb-2.5 font-medium transition-colors relative"
        :class="[activeTab === 'settings' ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800']"
        @click="activeTab = 'settings'"
      >
        Settings
        <span
          v-if="activeTab === 'settings'"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-full"
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
          <span class="text-slate-400">Connection status</span>
          <span class="inline-flex items-center gap-1.5 font-semibold text-slate-800">
            <CheckCircle2
              v-if="connection.status === 'connected'"
              :size="14"
              class="text-emerald-600"
            />
            {{ connection.status === 'connected' ? 'Connected' : 'Not configured' }}
          </span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400">Last sync</span>
          <span class="font-medium text-slate-800">{{ connection.lastSync }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400">Connected by</span>
          <span class="font-medium text-slate-800">{{ connection.connectedBy || '—' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400">Connected on</span>
          <span class="font-medium text-slate-800">{{ connection.connectedOn || '—' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400">Workspace</span>
          <span class="font-medium text-slate-800">{{ connection.workspace || 'NagareOS' }}</span>
        </div>
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400">Access type</span>
          <span class="font-medium text-slate-800">{{ connection.accessType || 'OAuth 2.0' }}</span>
        </div>
      </div>

      <!-- Sync History Section -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-xs font-bold text-slate-900">
            Sync history
          </h4>
          <button
            type="button"
            class="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700"
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
                class="text-emerald-600 shrink-0"
              />
              <span class="text-slate-800 truncate">{{ item.title }}</span>
            </div>
            <span class="text-[11px] text-slate-400 shrink-0 ml-2">{{ item.time }}</span>
          </div>
        </div>
        <p
          v-else
          class="text-xs text-slate-400 py-2"
        >
          No sync activity recorded yet.
        </p>
      </div>

      <!-- Enabled Capabilities Section -->
      <div>
        <div class="mb-3">
          <h4 class="text-xs font-bold text-slate-900">
            Enabled capabilities
          </h4>
          <p class="text-[11px] text-slate-500 mt-0.5">
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
              <div class="w-6 h-6 rounded-md bg-slate-100 flex items-center justify-center text-slate-600 shrink-0 mt-0.5">
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
                <p class="text-xs font-semibold text-slate-800 leading-tight">
                  {{ cap.title }}
                </p>
                <p class="text-[11px] text-slate-400 mt-0.5 leading-snug truncate">
                  {{ cap.description }}
                </p>
              </div>
            </div>

            <!-- Toggle Switch -->
            <button
              type="button"
              class="w-8 h-4.5 rounded-full transition-colors relative shrink-0 p-0.5 focus:outline-none"
              :class="cap.enabled ? 'bg-blue-600' : 'bg-slate-200'"
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
      <div class="pt-4 border-t border-slate-100 space-y-2">
        <button
          type="button"
          class="w-full py-2.5 rounded-xl bg-blue-50/80 hover:bg-blue-100/80 text-blue-600 text-xs font-semibold text-center transition-colors"
        >
          Configure connection
        </button>
        <button
          type="button"
          class="w-full py-1.5 text-xs font-medium text-red-500 hover:text-red-600 text-center transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>

    <!-- Tab: Permissions -->
    <div
      v-else-if="activeTab === 'permissions'"
      class="px-6 py-5 text-xs text-slate-600 space-y-3"
    >
      <p class="font-semibold text-slate-900">
        Active Scopes:
      </p>
      <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80 font-mono text-[11px] leading-relaxed">
        {{ connection.permissions }}
      </div>
      <p class="text-slate-400 text-[11px]">
        Tokens are secured using hardware-backed encryption keys and refreshed automatically.
      </p>
    </div>

    <!-- Tab: Data types -->
    <div
      v-else-if="activeTab === 'datatypes'"
      class="px-6 py-5 text-xs text-slate-600 space-y-3"
    >
      <p class="font-semibold text-slate-900">
        Indexed Types:
      </p>
      <div class="p-3 bg-slate-50 rounded-xl border border-slate-200/80 font-mono text-[11px] leading-relaxed">
        {{ connection.dataTypes }}
      </div>
    </div>

    <!-- Tab: Settings -->
    <div
      v-else
      class="px-6 py-5 text-xs text-slate-600 space-y-3"
    >
      <p class="font-semibold text-slate-900">
        Advanced Settings:
      </p>
      <p class="text-slate-500 text-xs">
        Webhook event subscription active. Polling fallback interval: 5 minutes.
      </p>
    </div>
  </aside>
</template>
