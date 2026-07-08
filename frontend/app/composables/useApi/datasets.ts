import type { Dataset } from '~/types'
import { useApiBase } from './utils'

export const useApiDatasets = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch<Dataset[]>('/api/datasets', { baseURL }),
    get: (id: string) => $fetch<Dataset>(`/api/datasets/${id}`, { baseURL }),
    create: (data: Partial<Dataset>) =>
      $fetch<Dataset>('/api/datasets', { method: 'POST', body: data, baseURL })
  }
}
