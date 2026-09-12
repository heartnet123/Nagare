<script setup lang="ts">
import { useConnections } from '~/composables/useConnections'
import ConnectionGrid from '~/components/connections/ConnectionGrid.vue'
import ConnectionSecurityBanner from '~/components/connections/ConnectionSecurityBanner.vue'
import ConnectionDetailPanel from '~/components/connections/ConnectionDetailPanel.vue'

definePageMeta({
  layout: 'default'
})

const {
  categories,
  activeFilter,
  searchQuery,
  detailPanelOpen,
  selectedConnectionId,
  selectedConnection,
  filteredConnections,
  selectConnection,
  toggleCapability,
  closeDetailPanel,
  openDetailPanel
} = useConnections()
</script>

<template>
  <div class="flex-1 min-h-0 flex flex-row overflow-hidden relative">
    <div class="flex-1 overflow-y-auto px-6 py-6 md:px-8 md:py-8 lg:px-10">
      <ConnectionGrid
        v-model:search-query="searchQuery"
        v-model:active-filter="activeFilter"
        :connections="filteredConnections"
        :categories="categories"
        :selected-connection-id="selectedConnectionId"
        :detail-panel-open="detailPanelOpen"
        @select-connection="selectConnection"
        @open-detail-panel="openDetailPanel"
      />

      <ConnectionSecurityBanner />
    </div>

    <ConnectionDetailPanel
      v-if="detailPanelOpen"
      :connection="selectedConnection"
      @close="closeDetailPanel"
      @toggle-capability="toggleCapability"
    />
  </div>
</template>
