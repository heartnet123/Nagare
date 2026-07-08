export interface Session {
  id: string
  name: string
  model: string
  endpoint_url: string
  rag: boolean
  archived: boolean
  is_important: boolean
  message_count: number
  created_at: string | null
  updated_at: string | null
  folder?: string
}
