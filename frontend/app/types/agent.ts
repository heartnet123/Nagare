export interface Agent {
  id: string
  name: string
  model: string
  type: 'chat' | 'rag' | 'search'
  status: 'active' | 'inactive'
  system_prompt?: string
  skills?: string[]
  role_title?: string
  category?: string
  description?: string
  tags?: string[]
  capabilities?: string[]
  tools?: string[]
  recent_wins?: Array<{
    title: string
    time: string
    date: string
  }>
  uses_count?: number
  completion_rate?: number
  requests?: number
  latency?: number
  created_at?: string
  updated_at?: string
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
