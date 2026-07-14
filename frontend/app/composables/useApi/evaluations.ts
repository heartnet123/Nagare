import { useApiBase } from './utils'

export const useApiEvaluations = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch('/api/evaluations/runs', { baseURL }),
    get: (id: string) => $fetch(`/api/evaluations/runs/${id}`, { baseURL }),
    create: (data: any) =>
      $fetch('/api/evaluations/runs', { method: 'POST', body: data, baseURL })
  }
}
