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
      })
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
    }
  }
}

