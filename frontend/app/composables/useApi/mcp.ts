import type { McpServer, McpServerForm } from '~/types'
import { useApiBase } from './utils'

export const useApiMcp = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch<McpServer[]>('/api/mcp/servers', { baseURL }),
    create: (data: McpServerForm) =>
      $fetch<McpServer>('/api/mcp/servers', { method: 'POST', body: data, baseURL }),
    update: (name: string, data: { command: string; args?: string[] }) =>
      $fetch<McpServer>(`/api/mcp/servers/${name}`, { method: 'PUT', body: data, baseURL }),
    delete: (name: string) =>
      $fetch(`/api/mcp/servers/${name}`, { method: 'DELETE', baseURL })
  }
}
