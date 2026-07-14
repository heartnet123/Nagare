<script setup lang="ts">
import { Activity, Server, Zap, AlertTriangle, CheckCircle2 } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const services = [
  { name: 'Retriever', uptime: '99.98%', latency: '82ms', status: 'healthy' as const },
  { name: 'Reranker', uptime: '99.95%', latency: '140ms', status: 'healthy' as const },
  { name: 'Vector Store', uptime: '99.99%', latency: '24ms', status: 'healthy' as const },
  { name: 'Generation', uptime: '99.82%', latency: '310ms', status: 'degraded' as const },
  { name: 'Embedding API', uptime: '100%', latency: '48ms', status: 'healthy' as const },
  { name: 'Orchestrator', uptime: '99.91%', latency: '18ms', status: 'healthy' as const }
]

const events = [
  { time: '14:32', text: 'Generation service latency exceeded 300ms threshold', tone: 'amber' as const },
  { time: '13:05', text: 'Auto-scaled retriever pool from 3 to 5 replicas', tone: 'blue' as const },
  { time: '11:47', text: 'Vector index rebuild completed (1.2M vectors)', tone: 'emerald' as const },
  { time: '09:20', text: 'Nightly evaluation suite passed (128/142 runs)', tone: 'emerald' as const }
]

function dotColor(tone: 'amber' | 'blue' | 'emerald') {
  return tone === 'amber' ? 'bg-amber-500' : tone === 'blue' ? 'bg-blue-500' : 'bg-emerald-500'
}
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Monitoring"
      description="Live health of every service in your RAG pipeline, with latency, throughput, and error-rate telemetry."
    >
      <template #action>
        <DashboardBadge tone="emerald">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          All systems operational
        </DashboardBadge>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="Zap"
        label="Requests / min"
        value="1.9K"
        trend="+6.2%"
      />
      <DashboardStatCard
        :icon="Activity"
        label="p95 Latency"
        value="340ms"
        trend="-8.4%"
      />
      <DashboardStatCard
        :icon="AlertTriangle"
        label="Error Rate"
        value="0.4%"
        trend="-0.1%"
      />
      <DashboardStatCard
        :icon="Server"
        label="Active Nodes"
        value="18"
        trend="+2"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
      <!-- Throughput -->
      <div class="p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm">
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
            Request Throughput
          </h3>
          <p class="text-xs text-stone-400 dark:text-stone-500">
            requests / min · last 24h
          </p>
        </div>
        <DashboardAreaChart
          :data="[900, 1100, 1000, 1350, 1600, 1400, 1700, 1500, 1850, 1900, 1750, 1900]"
          color="#00C16A"
        />
      </div>

      <!-- Latency -->
      <div class="p-5 rounded-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 shadow-sm">
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
            Latency (p95)
          </h3>
          <p class="text-xs text-stone-400 dark:text-stone-500">
            milliseconds · last 24h
          </p>
        </div>
        <DashboardAreaChart
          :data="[420, 400, 410, 360, 380, 350, 340, 355, 330, 340, 320, 340]"
          color="#00A155"
        />
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div class="lg:col-span-7">
        <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-stone-100 dark:border-stone-800">
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
              Service Health
            </h3>
          </div>
          <div class="divide-y divide-stone-100 dark:divide-stone-800">
            <div
              v-for="s in services"
              :key="s.name"
              class="flex items-center justify-between px-5 py-3.5"
            >
              <div class="flex items-center gap-3">
                <div
                  class="w-2 h-2 rounded-full"
                  :class="s.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500'"
                />
                <span class="text-sm font-medium text-stone-800 dark:text-stone-200">{{ s.name }}</span>
              </div>
              <div class="flex items-center gap-6 text-xs">
                <span class="text-stone-500 dark:text-stone-400">
                  <span class="text-stone-400 dark:text-stone-500">uptime </span>
                  {{ s.uptime }}
                </span>
                <span class="text-stone-500 dark:text-stone-400 w-16 text-right">
                  <span class="text-stone-400 dark:text-stone-500">p95 </span>
                  {{ s.latency }}
                </span>
                <DashboardBadge
                  v-if="s.status === 'healthy'"
                  tone="emerald"
                >
                  <CheckCircle2 :size="11" /> Healthy
                </DashboardBadge>
                <DashboardBadge
                  v-else
                  tone="amber"
                >
                  <AlertTriangle :size="11" /> Degraded
                </DashboardBadge>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="lg:col-span-5">
        <div class="bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-800 rounded-2xl shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-stone-100 dark:border-stone-800">
            <h3 class="text-sm font-semibold text-stone-900 dark:text-stone-100">
              Recent Events
            </h3>
          </div>
          <div class="divide-y divide-stone-100 dark:divide-stone-800">
            <div
              v-for="(e, i) in events"
              :key="i"
              class="flex items-start gap-3 px-5 py-3.5"
            >
              <span class="text-[11px] font-mono text-stone-400 dark:text-stone-500 pt-0.5 shrink-0">{{ e.time }}</span>
              <span
                class="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
                :class="dotColor(e.tone)"
              />
              <span class="text-xs text-stone-600 dark:text-stone-400 leading-relaxed">{{ e.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </DashboardPageScroll>
</template>
