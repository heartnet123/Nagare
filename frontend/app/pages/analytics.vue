<script setup lang="ts">
import { BarChart2, Users, MessageSquare, ThumbsUp } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const topQueries = [
  { q: 'How do I reset my API key?', count: 1284, trend: '+18%' },
  { q: 'What retrieval strategy works best for PDFs?', count: 964, trend: '+9%' },
  { q: 'Explain the reranking pipeline', count: 812, trend: '+22%' },
  { q: 'How is context precision calculated?', count: 640, trend: '+4%' },
  { q: 'Compare hybrid vs dense retrieval', count: 512, trend: '+31%' }
]
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Analytics"
      description="Usage, engagement, and answer-quality trends across your workspace over the last 7 days."
    >
      <template #action>
        <button class="flex items-center gap-2 px-4 py-2 rounded-xl border border-stone-200 bg-white hover:bg-stone-50 text-stone-700 text-sm font-medium shadow-sm transition-colors">
          <BarChart2
            :size="16"
            :stroke-width="1.5"
          />
          Last 7 days
        </button>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="MessageSquare"
        label="Total Queries"
        value="24.8K"
        trend="+12.5%"
      />
      <DashboardStatCard
        :icon="Users"
        label="Active Users"
        value="1,420"
        trend="+8.1%"
      />
      <DashboardStatCard
        :icon="ThumbsUp"
        label="Positive Feedback"
        value="94%"
        trend="+2.3%"
      />
      <DashboardStatCard
        :icon="BarChart2"
        label="Avg. Session"
        value="6.4m"
        trend="+0.8m"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-8">
      <div class="lg:col-span-7 p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-stone-900">
            Query Volume
          </h3>
          <p class="text-xs text-stone-400">
            queries per day · last 7 days
          </p>
        </div>
        <DashboardAreaChart
          :data="[2800, 3200, 3000, 3600, 4100, 3900, 4200]"
          color="#3b82f6"
          :height="180"
        />
      </div>
      <div class="lg:col-span-5 p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
        <div class="mb-4">
          <h3 class="text-sm font-semibold text-stone-900">
            Queries by Day
          </h3>
          <p class="text-xs text-stone-400">
            this week
          </p>
        </div>
        <DashboardBarChart
          :data="[2800, 3200, 3000, 3600, 4100, 3900, 4200]"
          :labels="['M', 'T', 'W', 'T', 'F', 'S', 'S']"
          color="#6366f1"
          :height="180"
        />
      </div>
    </div>

    <div class="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
      <div class="px-5 py-4 border-b border-stone-100">
        <h3 class="text-sm font-semibold text-stone-900">
          Top Queries
        </h3>
      </div>
      <div class="divide-y divide-stone-100">
        <div
          v-for="(t, i) in topQueries"
          :key="i"
          class="flex items-center gap-4 px-5 py-3.5"
        >
          <span class="text-xs font-mono text-stone-300 w-4 shrink-0">{{ i + 1 }}</span>
          <span class="text-sm text-stone-800 flex-1 truncate">{{ t.q }}</span>
          <span class="text-xs font-medium text-stone-500 shrink-0">
            {{ t.count.toLocaleString() }}
          </span>
          <span class="text-xs font-semibold text-emerald-600 w-12 text-right shrink-0">
            {{ t.trend }}
          </span>
        </div>
      </div>
    </div>
  </DashboardPageScroll>
</template>
