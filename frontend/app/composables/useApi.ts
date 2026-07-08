export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase || 'http://localhost:8000'

  return {
    evaluations: {
      list: () => $fetch('/api/evaluations/runs', { baseURL }),
      get: (id: string) => $fetch(`/api/evaluations/runs/${id}`, { baseURL }),
      create: (data: any) => $fetch('/api/evaluations/runs', {
        method: 'POST',
        body: data,
        baseURL
      })
    },
    agents: {
      list: () => $fetch('/api/agents', { baseURL }),
      get: (id: string) => $fetch(`/api/agents/${id}`, { baseURL }),
      create: (data: any) => $fetch('/api/agents', {
        method: 'POST',
        body: data,
        baseURL
      }),
      listSkills: () => $fetch('/api/agents/skills', { baseURL })
    },
    datasets: {
      list: () => $fetch('/api/datasets', { baseURL }),
      get: (id: string) => $fetch(`/api/datasets/${id}`, { baseURL }),
      create: (data: any) => $fetch('/api/datasets', {
        method: 'POST',
        body: data,
        baseURL
      })
    },
    monitoring: {
      getMetrics: () => $fetch('/api/monitoring/metrics', { baseURL })
    },
    logs: {
      list: () => $fetch('/api/logs', { baseURL })
    },
    sessions: {
      list: (search?: string) => $fetch<{ sessions: any[]; total: number }>('/api/sessions', { baseURL, query: { search } }),
      listArchived: (search?: string) => $fetch<{ sessions: any[]; total: number }>('/api/sessions/archived', { baseURL, query: { search } }),
      create: (data: { name?: string; model?: string; endpoint_url?: string }) => $fetch<any>('/api/session', {
        method: 'POST',
        body: data,
        baseURL
      }),
      get: (sid: string) => $fetch<any>(`/api/session/${sid}`, { baseURL }),
      update: (sid: string, data: { name?: string; folder?: string; model?: string }) => $fetch<any>(`/api/session/${sid}`, {
        method: 'PATCH',
        body: data,
        baseURL
      }),
      delete: (sid: string) => $fetch<any>(`/api/session/${sid}`, {
        method: 'DELETE',
        baseURL
      }),
      archive: (sid: string) => $fetch<any>(`/api/session/${sid}/archive`, {
        method: 'POST',
        baseURL
      }),
      unarchive: (sid: string) => $fetch<any>(`/api/session/${sid}/unarchive`, {
        method: 'POST',
        baseURL
      }),
      toggleImportant: (sid: string, important: boolean) => $fetch<any>(`/api/session/${sid}/important`, {
        method: 'POST',
        query: { important },
        baseURL
      }),
      getHistory: (sid: string) => $fetch<any[]>(`/api/history/${sid}`, { baseURL })
    },
    mcp: {
      list: () => $fetch('/api/mcp/servers', { baseURL }),
      create: (data: { name: string; command: string; args?: string[] }) => $fetch('/api/mcp/servers', {
        method: 'POST',
        body: data,
        baseURL
      }),
      update: (name: string, data: { command: string; args?: string[] }) => $fetch(`/api/mcp/servers/${name}`, {
        method: 'PUT',
        body: data,
        baseURL
      }),
      delete: (name: string) => $fetch(`/api/mcp/servers/${name}`, {
        method: 'DELETE',
        baseURL
      })
    },
    agentConfig: {
      get: () => $fetch('/api/agent/config', { baseURL }),
      update: (data: {
        base_url?: string
        api_key?: string
        model?: string
        max_rounds?: number
        workspace?: string
        system_prompt_append?: string
      }) => $fetch('/api/agent/config', { method: 'PUT', body: data, baseURL }),
      reset: () => $fetch('/api/agent/config', { method: 'DELETE', baseURL })
    }
  }
}

