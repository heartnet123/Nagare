<script setup lang="ts">
import { Bot, Activity } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const agents = [
  { name: 'Retrieval Agent', role: 'Fetches candidate chunks from the vector store', tasks: 8420, latency: '82ms', status: 'healthy', load: [20, 30, 25, 40, 35, 45, 42] },
  { name: 'Reranking Agent', role: 'Reorders chunks by cross-encoder relevance', tasks: 8420, latency: '140ms', status: 'healthy', load: [30, 35, 32, 38, 40, 44, 41] },
  { name: 'Synthesis Agent', role: 'Generates grounded answers from context', tasks: 8410, latency: '310ms', status: 'busy', load: [50, 55, 60, 58, 65, 70, 68] },
  { name: 'Router Agent', role: 'Classifies intent and routes queries', tasks: 8500, latency: '18ms', status: 'healthy', load: [10, 12, 11, 14, 13, 15, 14] },
  { name: 'Guardrail Agent', role: 'Filters unsafe or off-topic requests', tasks: 8500, latency: '22ms', status: 'healthy', load: [8, 9, 10, 9, 11, 10, 12] },
  { name: 'Feedback Agent', role: 'Collects and scores user feedback', tasks: 3210, latency: '30ms', status: 'idle', load: [5, 4, 6, 5, 7, 6, 5] }
]
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Agents"
      description="The autonomous workers that power your pipeline. Monitor load, latency, and health for each agent."
    >
      <template #action>
        <DashboardBadge tone="emerald">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          12 online
        </DashboardBadge>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="Bot"
        label="Active Agents"
        value="12"
        trend="+0"
      />
      <DashboardStatCard
        :icon="Activity"
        label="Tasks / min"
        value="1.9K"
        :trend-positive="true"
        trend="+6.2%"
      />
      <DashboardStatCard
        :icon="Activity"
        label="Avg. Latency"
        value="86ms"
        :trend-positive="true"
        trend="-4.1%"
      />
      <DashboardStatCard
        :icon="Bot"
        label="Idle Agents"
        value="1"
      />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="a in agents"
        :key="a.name"
        class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Bot
                :size="20"
                :stroke-width="1.5"
              />
            </div>
            <div>
              <h4 class="text-sm font-semibold text-stone-900">
                {{ a.name }}
              </h4>
              <p class="text-xs text-stone-500 mt-0.5 max-w-[220px] leading-relaxed">
                {{ a.role }}
              </p>
            </div>
          </div>
          <DashboardBadge
            v-if="a.status === 'healthy'"
            tone="emerald"
          >
            Healthy
          </DashboardBadge>
          <DashboardBadge
            v-else-if="a.status === 'busy'"
            tone="amber"
          >
            Busy
          </DashboardBadge>
          <DashboardBadge v-else-if="a.status === 'idle'">
            Idle
          </DashboardBadge>
        </div>
        <div class="flex items-end justify-between gap-4 pt-3 border-t border-stone-100">
          <div class="flex gap-6 text-xs">
            <div class="flex flex-col">
              <span class="text-stone-400">Tasks</span>
              <span class="font-semibold text-stone-800">{{ a.tasks.toLocaleString() }}</span>
            </div>
            <div class="flex flex-col">
              <span class="text-stone-400">Latency</span>
              <span class="font-semibold text-stone-800">{{ a.latency }}</span>
            </div>
          </div>
          <div class="w-24 h-8">
            <DashboardSparkline
              :data="a.load"
              color="#3b82f6"
            />
          </div>
        </div>
      </div>
    </div>
  </DashboardPageScroll>
</template>
