<script setup lang="ts">
import { Database, Plus, FileText, Upload, MoreHorizontal } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const datasets = [
  { name: 'legal-docs', desc: 'Contracts, filings, and case law for legal QA evaluation.', cases: 240, docs: '1.2K', updated: '2 hours ago', tone: 'blue' as const },
  { name: 'support-tickets', desc: 'Historical customer support conversations and resolutions.', cases: 512, docs: '4.8K', updated: '1 day ago', tone: 'emerald' as const },
  { name: 'product-manuals', desc: 'Technical documentation and troubleshooting guides.', cases: 180, docs: '860', updated: '3 days ago', tone: 'amber' as const },
  { name: 'research-papers', desc: 'Academic papers on retrieval and generation methods.', cases: 96, docs: '340', updated: '5 days ago', tone: 'purple' as const },
  { name: 'onboarding', desc: 'Internal onboarding and HR knowledge base articles.', cases: 64, docs: '210', updated: '1 week ago', tone: 'blue' as const },
  { name: 'sales-playbook', desc: 'Sales enablement content and objection handling scripts.', cases: 120, docs: '540', updated: '2 weeks ago', tone: 'emerald' as const }
]
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Datasets"
      description="Curated collections of question-answer pairs and documents used to benchmark and evaluate your retrieval pipeline."
    >
      <template #action>
        <div class="flex items-center gap-2">
          <button class="flex items-center gap-2 px-4 py-2 rounded-xl border border-stone-200 bg-white hover:bg-stone-50 text-stone-700 text-sm font-medium shadow-sm transition-colors">
            <Upload
              :size="16"
              :stroke-width="1.5"
            />
            Import
          </button>
          <button class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm transition-colors">
            <Plus
              :size="16"
              :stroke-width="2"
            />
            New Dataset
          </button>
        </div>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <DashboardStatCard
        :icon="Database"
        label="Total Datasets"
        value="18"
        trend="+3"
      />
      <DashboardStatCard
        :icon="FileText"
        label="Total Documents"
        value="7.9K"
        trend="+412"
      />
      <DashboardStatCard
        :icon="FileText"
        label="Test Cases"
        value="1,212"
        trend="+86"
      />
      <DashboardStatCard
        :icon="Upload"
        label="Storage Used"
        value="4.2 GB"
        trend="+0.3 GB"
      />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="d in datasets"
        :key="d.name"
        class="flex flex-col p-5 rounded-2xl bg-white border border-stone-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="p-2.5 rounded-xl bg-stone-50 text-stone-600">
            <Database
              :size="20"
              :stroke-width="1.5"
            />
          </div>
          <button
            class="p-1 text-stone-300 hover:text-stone-600"
            aria-label="More options"
          >
            <MoreHorizontal :size="18" />
          </button>
        </div>
        <h4 class="text-sm font-semibold text-stone-900 mb-1">
          {{ d.name }}
        </h4>
        <p class="text-xs text-stone-500 leading-relaxed mb-4 flex-1">
          {{ d.desc }}
        </p>
        <div class="flex items-center gap-2 mb-4">
          <DashboardBadge :tone="d.tone">
            {{ d.cases }} cases
          </DashboardBadge>
          <DashboardBadge>{{ d.docs }} docs</DashboardBadge>
        </div>
        <div class="text-[11px] text-stone-400 pt-3 border-t border-stone-100">
          Updated {{ d.updated }}
        </div>
      </div>
    </div>
  </DashboardPageScroll>
</template>
