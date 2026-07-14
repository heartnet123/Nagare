import { useApiBase } from './utils'

export const useApiLogs = () => {
  const baseURL = useApiBase()

  return {
    list: () => $fetch('/api/logs', { baseURL })
  }
}
