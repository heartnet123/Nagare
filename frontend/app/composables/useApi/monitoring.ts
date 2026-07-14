import type { SystemMetrics } from '~/types'
import { useApiBase } from './utils'

export const useApiMonitoring = () => {
  const baseURL = useApiBase()

  return {
    getMetrics: () => $fetch<SystemMetrics>('/api/monitoring/metrics', { baseURL })
  }
}
