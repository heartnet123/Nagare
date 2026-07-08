<script setup lang="ts">
import { CheckCircle2, XCircle, Clock, Play, TrendingUp } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const runs = [
  { id: 'run-8842', dataset: 'legal-docs', cases: 240, faithfulness: 0.91, relevance: 0.88, precision: 0.86, status: 'passed', time: '2 min ago' },
  { id: 'run-8841', dataset: 'support-tickets', cases: 512, faithfulness: 0.87, relevance: 0.9, precision: 0.83, status: 'passed', time: '1 hour ago' },
  { id: 'run-8840', dataset: 'product-manuals', cases: 180, faithfulness: 0.79, relevance: 0.81, precision: 0.74, status: 'failed', time: '3 hours ago' },
  { id: 'run-8839', dataset: 'research-papers', cases: 96, faithfulness: 0.93, relevance: 0.89, precision: 0.88, status: 'passed', time: '5 hours ago' },
  { id: 'run-8838', dataset: 'legal-docs', cases: 240, faithfulness: 0.9, relevance: 0.86, precision: 0.85, status: 'passed', time: 'Yesterday' },
  { id: 'run-8837', dataset: 'onboarding', cases: 64, faithfulness: 0.72, relevance: 0.7, precision: 0.68, status: 'failed', time: 'Yesterday' }
]

function getScoreTone(v: number) {
  return v >= 0.85 ? 'text-emerald-600' : v >= 0.75 ? 'text-amber-600' : 'text-red-500'
}
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Evaluations"
      description="Score your RAG pipeline against curated datasets. Track faithfulness, answer relevance, and context precision across every run."
    >
      <template #action>
        <button class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-colors">
          <Play
            :size="16"
            :stroke-width="2"
          />
          New Evaluation
        </button>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="TrendingUp"
        label="Avg. Faithfulness"
        value="0.89"
        trend="+0.03"
      />
      <DashboardStatCard
        :icon="CheckCircle2"
        label="Passed Runs"
        value="128"
        trend="+11"
      />
      <DashboardStatCard
        :icon="XCircle"
        label="Failed Runs"
        value="14"
        trend="-4"
        :trend-positive="false"
      />
      <DashboardStatCard
        :icon="Clock"
        label="Avg. Duration"
        value="4.2m"
        trend="-0.6m"
      />
    </div>

    <div class="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden mb-10">
      <div class="flex items-center justify-between px-5 py-4 border-b border-stone-100">
        <h3 class="text-sm font-semibold text-stone-900">
          Recent Runs
        </h3>
        <span class="text-xs text-stone-400">142 total</span>
      </div>
      <div class="overflow-x-auto hide-scrollbar">
        <table class="w-full text-sm min-w-[720px]">
          <thead>
            <tr class="text-left text-[11px] uppercase tracking-wider text-stone-400">
              <th class="font-medium px-5 py-3">
                Run
              </th>
              <th class="font-medium px-5 py-3">
                Dataset
              </th>
              <th class="font-medium px-5 py-3">
                Cases
              </th>
              <th class="font-medium px-5 py-3">
                Faithfulness
              </th>
              <th class="font-medium px-5 py-3">
                Relevance
              </th>
              <th class="font-medium px-5 py-3">
                Precision
              </th>
              <th class="font-medium px-5 py-3">
                Status
              </th>
              <th class="font-medium px-5 py-3">
                When
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in runs"
              :key="r.id"
              class="border-t border-stone-100 hover:bg-stone-50 transition-colors"
            >
              <td class="px-5 py-3.5 font-mono text-xs text-stone-500">
                {{ r.id }}
              </td>
              <td class="px-5 py-3.5 font-medium text-stone-800">
                {{ r.dataset }}
              </td>
              <td class="px-5 py-3.5 text-stone-600">
                {{ r.cases }}
              </td>
              <td class="px-5 py-3.5">
                <span
                  class="font-semibold"
                  :class="getScoreTone(r.faithfulness)"
                >{{ r.faithfulness.toFixed(2) }}</span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  class="font-semibold"
                  :class="getScoreTone(r.relevance)"
                >{{ r.relevance.toFixed(2) }}</span>
              </td>
              <td class="px-5 py-3.5">
                <span
                  class="font-semibold"
                  :class="getScoreTone(r.precision)"
                >{{ r.precision.toFixed(2) }}</span>
              </td>
              <td class="px-5 py-3.5">
                <DashboardBadge
                  v-if="r.status === 'passed'"
                  tone="emerald"
                >
                  <CheckCircle2 :size="11" /> Passed
                </DashboardBadge>
                <DashboardBadge
                  v-else
                  tone="red"
                >
                  <XCircle :size="11" /> Failed
                </DashboardBadge>
              </td>
              <td class="px-5 py-3.5 text-stone-400 whitespace-nowrap">
                {{ r.time }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
      <!-- Faithfulness Trend -->
      <div class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-stone-500 font-medium">Faithfulness</span>
          <span class="text-lg font-semibold text-stone-900">0.89</span>
        </div>
        <div class="h-12">
          <DashboardSparkline
            :data="[0.82, 0.84, 0.83, 0.86, 0.88, 0.87, 0.89]"
            color="#3b82f6"
          />
        </div>
      </div>

      <!-- Answer Relevance Trend -->
      <div class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-stone-500 font-medium">Answer Relevance</span>
          <span class="text-lg font-semibold text-stone-900">0.86</span>
        </div>
        <div class="h-12">
          <DashboardSparkline
            :data="[0.8, 0.82, 0.81, 0.84, 0.85, 0.85, 0.86]"
            color="#3b82f6"
          />
        </div>
      </div>

      <!-- Context Precision Trend -->
      <div class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs text-stone-500 font-medium">Context Precision</span>
          <span class="text-lg font-semibold text-stone-900">0.84</span>
        </div>
        <div class="h-12">
          <DashboardSparkline
            :data="[0.75, 0.78, 0.79, 0.8, 0.82, 0.83, 0.84]"
            color="#3b82f6"
          />
        </div>
      </div>
    </div>
  </DashboardPageScroll>
</template>
