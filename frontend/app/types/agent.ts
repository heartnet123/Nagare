export interface Agent {
  id: string
  name: string
  model: string
  type: 'chat' | 'rag' | 'search'
  status: 'active' | 'inactive'
  system_prompt?: string
  skills?: string[]
  requests?: number
  latency?: number
}

export interface Skill {
  name: string
  title?: string
  description?: string
}

export interface AgentConfig {
  base_url?: string
  api_key?: string
  model?: string
  max_rounds?: number
  workspace?: string
  system_prompt_append?: string
}
