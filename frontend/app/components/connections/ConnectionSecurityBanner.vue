<script setup lang="ts">
import { Shield, ArrowRight } from '@lucide/vue'
</script>

<template>
  <div class="mt-8 rounded-2xl border border-blue-100 bg-blue-50/40 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div class="flex items-start sm:items-center gap-3.5">
      <div class="w-10 h-10 rounded-xl bg-blue-100/60 flex items-center justify-center text-blue-600 shrink-0">
        <Shield
          :size="20"
          :stroke-width="2"
        />
      </div>
      <div>
        <h4 class="text-xs sm:text-sm font-bold text-slate-900 leading-tight">
          Your data stays secure
        </h4>
        <p class="text-[11px] sm:text-xs text-slate-500 mt-0.5 leading-relaxed max-w-3xl">
          We use industry-standard encryption and follow the principle of least privilege. You can review and revoke access at any time. All access is logged in the audit trail.
        </p>
      </div>
    </div>
    <button
      type="button"
      class="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 shrink-0 self-start sm:self-center"
    >
      <span>View security details</span>
      <ArrowRight :size="14" />
    </button>
  </div>
</template>
