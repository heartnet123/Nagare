<script setup lang="ts">
import { Cpu } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="MCP Servers"
      description="Configure custom Model Context Protocol (MCP) servers. Custom servers enable your AI agents to interact with localized resources, run shell utilities, access files, or interface with external APIs."
    >
      <template #action>
        <div class="flex items-center gap-2">
          <DashboardBadge tone="blue">
            <span class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            JSON-RPC Stdio Enabled
          </DashboardBadge>
        </div>
      </template>
    </DashboardPageHeader>

    <div class="max-w-5xl">
      <McpManager />
    </div>
  </DashboardPageScroll>
</template>
