import type { Agent, Skill, AgentConfig } from '~/types'
import { useApiBase } from './utils'

export const useApiAgents = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch<Agent[]>('/api/agents', { baseURL }),
    get: (id: string) => $fetch<Agent>(`/api/agents/${id}`, { baseURL }),
    create: (data: Partial<Agent>) =>
      $fetch<Agent>('/api/agents', { method: 'POST', body: data, baseURL }),
    update: (id: string, data: Partial<Agent>) =>
      $fetch<Agent>(`/api/agents/${id}`, { method: 'PUT', body: data, baseURL }),
    delete: (id: string) =>
      $fetch(`/api/agents/${id}`, { method: 'DELETE', baseURL }),
    listSkills: () => $fetch<Skill[]>('/api/agents/skills', { baseURL })
  }
}

export const useApiAgentConfig = () => {
  const baseURL = useApiBase()

  return {
    get: () => $fetch<AgentConfig>('/api/agent/config', { baseURL }),
    update: (data: AgentConfig) =>
      $fetch('/api/agent/config', { method: 'PUT', body: data, baseURL }),
    reset: () =>
      $fetch('/api/agent/config', { method: 'DELETE', baseURL })
  }
}
