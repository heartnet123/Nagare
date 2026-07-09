import type { Model } from '~/types'
import { useApiBase } from './utils'

export const useApiModels = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch<Model[]>('/api/models', { baseURL }),
    getCurrent: () => $fetch<{ id: string; name: string; provider: string }>('/api/models/current', { baseURL })
  }
}
