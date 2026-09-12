import { ref, computed } from 'vue'
import { INITIAL_CONNECTIONS, CONNECTION_CATEGORIES } from '~/constants/connections'
import type { Connection, ConnectionTab } from '~/types/connection'

export function useConnections() {
  const connections = ref<Connection[]>(JSON.parse(JSON.stringify(INITIAL_CONNECTIONS)))
  const activeFilter = ref<string>('All')
  const searchQuery = ref('')
  const detailPanelOpen = ref(true)
  const activeTab = ref<ConnectionTab>('overview')
  const selectedConnectionId = ref('slack')

  const selectedConnection = computed<Connection>(() => {
    return connections.value.find(c => c.id === selectedConnectionId.value) || (connections.value[0] as Connection)
  })

  const filteredConnections = computed(() => {
    return connections.value.filter((item) => {
      if (activeFilter.value === 'Active' && item.status !== 'connected') return false
      if (activeFilter.value === 'Recommended' && !item.recommended) return false
      if (
        activeFilter.value !== 'All'
        && activeFilter.value !== 'Active'
        && activeFilter.value !== 'Recommended'
        && item.category !== activeFilter.value
      ) {
        return false
      }

      if (searchQuery.value.trim()) {
        const q = searchQuery.value.toLowerCase().trim()
        const matchName = item.name.toLowerCase().includes(q)
        const matchDesc = item.description.toLowerCase().includes(q)
        const matchData = item.dataTypes.toLowerCase().includes(q)
        return matchName || matchDesc || matchData
      }

      return true
    })
  })

  const selectConnection = (conn: Connection) => {
    selectedConnectionId.value = conn.id
    detailPanelOpen.value = true
  }

  const toggleCapability = (capId: string) => {
    const cap = selectedConnection.value.capabilities.find(c => c.id === capId)
    if (cap) {
      cap.enabled = !cap.enabled
    }
  }

  const closeDetailPanel = () => {
    detailPanelOpen.value = false
  }

  const openDetailPanel = () => {
    detailPanelOpen.value = true
  }

  return {
    categories: CONNECTION_CATEGORIES,
    connections,
    activeFilter,
    searchQuery,
    detailPanelOpen,
    activeTab,
    selectedConnectionId,
    selectedConnection,
    filteredConnections,
    selectConnection,
    toggleCapability,
    closeDetailPanel,
    openDetailPanel
  }
}
