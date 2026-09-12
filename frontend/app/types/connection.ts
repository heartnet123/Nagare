export type ConnectionCategory = 'Communication' | 'Docs' | 'Data' | 'Dev Tools'

export type ConnectionStatus = 'connected' | 'available'

export interface SyncRecord {
  id: string
  title: string
  time: string
}

export interface Capability {
  id: string
  title: string
  description: string
  enabled: boolean
  icon: string
}

export interface Connection {
  id: string
  name: string
  category: ConnectionCategory
  description: string
  longDescription: string
  status: ConnectionStatus
  recommended?: boolean
  lastSync: string
  permissions: string
  dataTypes: string
  connectedBy?: string
  connectedOn?: string
  workspace?: string
  accessType?: string
  syncHistory: SyncRecord[]
  capabilities: Capability[]
}

export type ConnectionTab = 'overview' | 'permissions' | 'datatypes' | 'settings'
