import { useApiBase } from './utils'

export interface RegistryModel {
  id: string
  name: string
  provider: string
  description: string | null
  input_cost_per_1m: number
  output_cost_per_1m: number
  max_context_length: number
  is_active: boolean
  config: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface UsageStats {
  model_id: string
  model_name: string
  total_input_tokens: number
  total_output_tokens: number
  total_cost: number
  request_count: number
  last_used: string | null
}

export interface UsageSummary {
  models: UsageStats[]
  total_input_tokens: number
  total_output_tokens: number
  total_cost: number
}

export const useApiModels = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch<RegistryModel[]>('/api/models', { baseURL }),
    getCurrent: () => $fetch<{ id: string, name: string, provider: string }>('/api/models/current', { baseURL }),
    usageSummary: () => $fetch<UsageSummary>('/api/models/usage/summary', { baseURL }),
    config: () => $fetch<Record<string, unknown>>('/api/models/config', { baseURL })
  }
}
