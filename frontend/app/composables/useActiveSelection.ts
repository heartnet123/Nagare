import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { Model, Agent } from '~/types'

export const useActiveSelection = () => {
  const selectedModel = useState<Model | null>('active-selection:model', () => null)
  const selectedAgent = useState<Agent | null>('active-selection:agent', () => null)
  const models = useState<Model[]>('active-selection:models-list', () => [])
  const agents = useState<Agent[]>('active-selection:agents-list', () => [])
  const loadingModels = useState<boolean>('active-selection:loading-models', () => false)
  const loadingAgents = useState<boolean>('active-selection:loading-agents', () => false)
  const initialized = useState<boolean>('active-selection:initialized', () => false)

  const api = useApi()
  const route = useRoute()
  const sessionStore = useSessionStore()

  // Track active session ID from route params, query, or drawer session state
  const activeSessionId = computed(() => {
    if (route.params.id) {
      return route.params.id as string
    }
    if (route.query.session) {
      return route.query.session as string
    }
    if (sessionStore.drawerSessionId.value) {
      return sessionStore.drawerSessionId.value
    }
    return null
  })

  async function loadModels() {
    loadingModels.value = true
    try {
      models.value = await api.models.list()
    } catch (error) {
      console.error('Failed to load models:', error)
    } finally {
      loadingModels.value = false
    }
  }

  async function loadAgents() {
    loadingAgents.value = true
    try {
      agents.value = await api.agents.list()
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      loadingAgents.value = false
    }
  }

  async function updateSessionModel(modelName: string) {
    const sid = activeSessionId.value
    if (!sid) return
    try {
      await api.sessions.update(sid, { model: modelName })
      // Reload sessions list to keep sidebar updated
      await sessionStore.loadSessions()
    } catch (error) {
      console.error('Failed to update session model on backend:', error)
    }
  }

  function selectModel(model: Model) {
    selectedModel.value = model
    selectedAgent.value = null
    localStorage.setItem('nagare:active-selection', JSON.stringify({ type: 'model', id: model.id }))
    updateSessionModel(model.id)
  }

  function selectAgent(agent: Agent) {
    selectedAgent.value = agent
    selectedModel.value = null
    localStorage.setItem('nagare:active-selection', JSON.stringify({ type: 'agent', id: agent.id }))
    updateSessionModel(agent.model) // when selecting an agent, update session to use agent's model
  }

  function restoreSelection() {
    const saved = localStorage.getItem('nagare:active-selection')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (parsed.type === 'model') {
          const found = models.value.find(m => m.id === parsed.id)
          if (found) {
            selectedModel.value = found
            selectedAgent.value = null
            return
          }
        } else if (parsed.type === 'agent') {
          const found = agents.value.find(a => a.id === parsed.id)
          if (found) {
            selectedAgent.value = found
            selectedModel.value = null
            return
          }
        }
      } catch (e) {
        console.error('Failed to parse active selection from localStorage', e)
      }
    }

    // Default fallback: select first available model
    if (models.value.length > 0) {
      selectedModel.value = models.value[0] || null
      selectedAgent.value = null
    }
  }

  function syncSelectionToModel(modelName: string | null | undefined) {
    if (!modelName) return

    // Try finding matching agent by model or name
    const foundAgent = agents.value.find(a => a.model === modelName || a.name === modelName)
    if (foundAgent) {
      selectedAgent.value = foundAgent
      selectedModel.value = null
      return
    }

    // Otherwise try finding matching model by id or name
    const foundModel = models.value.find(m => m.id === modelName || m.name === modelName)
    if (foundModel) {
      selectedModel.value = foundModel
      selectedAgent.value = null
    }
  }

  const activeModelName = computed(() => {
    if (selectedAgent.value) {
      return selectedAgent.value.model
    }
    if (selectedModel.value) {
      return selectedModel.value.id
    }
    return null
  })

  const displayText = computed(() => {
    if (selectedAgent.value) {
      return selectedAgent.value.name
    }
    if (selectedModel.value) {
      return selectedModel.value.name
    }
    return 'Select model'
  })

  async function init() {
    if (initialized.value) return
    await Promise.all([loadModels(), loadAgents()])
    restoreSelection()
    initialized.value = true
  }

  return {
    selectedModel,
    selectedAgent,
    models,
    agents,
    loadingModels,
    loadingAgents,
    loadModels,
    loadAgents,
    selectModel,
    selectAgent,
    restoreSelection,
    syncSelectionToModel,
    activeModelName,
    displayText,
    init
  }
}
