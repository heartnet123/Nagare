import { useApiBase } from './utils'

export interface DecisionAlternative {
  id: string
  label: string
  name: string
  description?: string
  estimated_reach?: string
  estimated_cost?: string
  expected_lift?: string
  timeline?: string
  recommended?: boolean
}

export interface DecisionMaterial {
  name: string
  size: string
  type: string
}

export interface DecisionItem {
  id: string
  user_id?: string
  title: string
  subtitle: string
  priority: string
  priority_label: string
  time_ago: string
  agent_name: string
  agent_role: string
  agent_initials: string
  agent_color: string
  comments_count: number
  category: string
  project: string
  confidence_score: number
  summary: string
  key_rationale: string[]
  potential_risks: string[]
  alternatives: DecisionAlternative[]
  files: DecisionMaterial[]
  status: 'pending' | 'approved' | 'sent_back' | 'rejected'
  selected_alternative: string
  created_at: string
  updated_at: string
}

export interface InboxStats {
  avg_time: string
  avg_time_change: string
  pending_count: number
  sla_risk_count: number
  approved_count: number
  sent_back_count: number
  urgent_count: number
  today_count: number
  this_week_count: number
  total_pending: number
}

export const useApiInbox = () => {
  const baseURL = useApiBase()

  return {
    list: (filter = 'all', search?: string) =>
      $fetch<DecisionItem[]>('/api/inbox/decisions', { baseURL, query: { filter, search } }),
    stats: () =>
      $fetch<InboxStats>('/api/inbox/stats', { baseURL }),
    get: (id: string) =>
      $fetch<DecisionItem>(`/api/inbox/decisions/${id}`, { baseURL }),
    create: (data: Partial<DecisionItem>) =>
      $fetch<DecisionItem>('/api/inbox/decisions', { method: 'POST', baseURL, body: data }),
    patch: (id: string, data: { selected_alternative?: string, status?: string }) =>
      $fetch<DecisionItem>(`/api/inbox/decisions/${id}`, { method: 'PATCH', baseURL, body: data }),
    approve: (id: string) =>
      $fetch<{ status: string, new_status: string, decision_id: string }>(`/api/inbox/decisions/${id}/approve`, {
        method: 'POST',
        baseURL
      }),
    requestChanges: (id: string, note?: string) =>
      $fetch<{ status: string, new_status: string, decision_id: string }>(`/api/inbox/decisions/${id}/request-changes`, {
        method: 'POST',
        baseURL,
        body: { note }
      }),
    assignBack: (id: string) =>
      $fetch<{ status: string, new_status: string, decision_id: string }>(`/api/inbox/decisions/${id}/assign-back`, {
        method: 'POST',
        baseURL
      }),
    remove: (id: string) =>
      $fetch<{ status: string, deleted: boolean, decision_id: string }>(`/api/inbox/decisions/${id}`, {
        method: 'DELETE',
        baseURL
      })
  }
}
