<script setup lang="ts">
import { FileText, CheckCircle2, AlertTriangle, XCircle } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const logs = [
  { id: 'q_9f2a', query: 'Explain the architecture of RAG systems', latency: '284ms', chunks: 5, score: 0.94, level: 'ok' as const, time: '14:32:08' },
  { id: 'q_9f29', query: 'Compare retrieval strategies for legal documents', latency: '412ms', chunks: 8, score: 0.88, level: 'ok' as const, time: '14:31:55' },
  { id: 'q_9f28', query: 'What are the latest papers about multi-agent RAG?', latency: '620ms', chunks: 6, score: 0.71, level: 'warn' as const, time: '14:31:40' },
  { id: 'q_9f27', query: 'Summarize the Q3 benchmark results', latency: '198ms', chunks: 4, score: 0.91, level: 'ok' as const, time: '14:31:12' },
  { id: 'q_9f26', query: 'How does reranking affect precision?', latency: '1240ms', chunks: 0, score: 0.0, level: 'error' as const, time: '14:30:47' },
  { id: 'q_9f25', query: 'List all onboarding documents', latency: '156ms', chunks: 3, score: 0.86, level: 'ok' as const, time: '14:30:20' },
  { id: 'q_9f24', query: 'Explain context precision metric', latency: '332ms', chunks: 5, score: 0.79, level: 'warn' as const, time: '14:29:58' }
]

function getScoreTone(score: number) {
  return score >= 0.85 ? 'text-emerald-600 font-semibold' : score >= 0.75 ? 'text-amber-600 font-semibold' : 'text-red-500 font-semibold'
}
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Logs"
      description="A detailed request log of every query processed by the pipeline, including latency, retrieved chunks, and relevance score."
    >
      <template #action>
        <div class="flex items-center gap-2">
          <DashboardBadge tone="emerald">
            <CheckCircle2 :size="11" /> OK
          </DashboardBadge>
          <DashboardBadge tone="amber">
            <AlertTriangle :size="11" /> Warn
          </DashboardBadge>
          <DashboardBadge tone="red">
            <XCircle :size="11" /> Error
          </DashboardBadge>
        </div>
      </template>
    </DashboardPageHeader>

    <div class="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
      <div class="flex items-center gap-2 px-5 py-4 border-b border-stone-100">
        <FileText
          :size="16"
          class="text-stone-400"
        />
        <h3 class="text-sm font-semibold text-stone-900">
          Query Log
        </h3>
        <span class="ml-auto text-xs text-stone-400">Live · 18.2K today</span>
      </div>
      <div class="overflow-x-auto hide-scrollbar">
        <table class="w-full text-sm min-w-[760px]">
          <thead>
            <tr class="text-left text-[11px] uppercase tracking-wider text-stone-400">
              <th class="font-medium px-5 py-3">
                Time
              </th>
              <th class="font-medium px-5 py-3">
                ID
              </th>
              <th class="font-medium px-5 py-3">
                Query
              </th>
              <th class="font-medium px-5 py-3">
                Latency
              </th>
              <th class="font-medium px-5 py-3">
                Chunks
              </th>
              <th class="font-medium px-5 py-3">
                Score
              </th>
              <th class="font-medium px-5 py-3">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="l in logs"
              :key="l.id"
              class="border-t border-stone-100 hover:bg-stone-50 transition-colors"
            >
              <td class="px-5 py-3.5 font-mono text-xs text-stone-400 whitespace-nowrap">
                {{ l.time }}
              </td>
              <td class="px-5 py-3.5 font-mono text-xs text-stone-500">
                {{ l.id }}
              </td>
              <td class="px-5 py-3.5 text-stone-800 max-w-xs truncate">
                {{ l.query }}
              </td>
              <td class="px-5 py-3.5 text-stone-600 whitespace-nowrap">
                {{ l.latency }}
              </td>
              <td class="px-5 py-3.5 text-stone-600">
                {{ l.chunks }}
              </td>
              <td class="px-5 py-3.5">
                <span :class="getScoreTone(l.score)">
                  {{ l.score.toFixed(2) }}
                </span>
              </td>
              <td class="px-5 py-3.5">
                <DashboardBadge
                  v-if="l.level === 'ok'"
                  tone="emerald"
                >
                  <CheckCircle2 :size="11" /> OK
                </DashboardBadge>
                <DashboardBadge
                  v-else-if="l.level === 'warn'"
                  tone="amber"
                >
                  <AlertTriangle :size="11" /> Warn
                </DashboardBadge>
                <DashboardBadge
                  v-else-if="l.level === 'error'"
                  tone="red"
                >
                  <XCircle :size="11" /> Error
                </DashboardBadge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </DashboardPageScroll>
</template>
