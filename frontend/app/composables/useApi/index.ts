/**
 * Domain-split API composables.
 *
 * Use individual composables for focused access:
 *   const { list } = useApiEvaluations()
 *
 * Or use barrel for convenience:
 *   const api = useApi()
 *   api.evaluations.list()
 */
import { useApiEvaluations } from './evaluations'
import { useApiAgents, useApiAgentConfig } from './agents'
import { useApiDatasets } from './datasets'
import { useApiSessions } from './sessions'
import { useApiMcp } from './mcp'
import { useApiLogs } from './logs'
import { useApiMonitoring } from './monitoring'

export {
  useApiEvaluations,
  useApiAgents,
  useApiAgentConfig,
  useApiDatasets,
  useApiSessions,
  useApiMcp,
  useApiLogs,
  useApiMonitoring
}

/**
 * Legacy barrel — returns the same flat API object as the original useApi().
 * New code should import individual composables instead.
 */
export const useApi = () => {
  const evaluations = useApiEvaluations()
  const agents = useApiAgents()
  const agentConfig = useApiAgentConfig()
  const datasets = useApiDatasets()
  const sessions = useApiSessions()
  const mcp = useApiMcp()
  const logs = useApiLogs()
  const monitoring = useApiMonitoring()

  return {
    evaluations,
    agents,
    agentConfig,
    datasets,
    sessions,
    mcp,
    logs,
    monitoring
  }
}
