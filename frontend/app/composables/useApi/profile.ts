import { useApiBase } from './utils'

export interface ConnectedAccount {
  provider: string
  account_name: string
  status: string
}

export interface CompletionItem {
  id: string
  label: string
  completed: boolean
}

export interface ActivityItem {
  id: string
  title: string
  time_ago: string
  type: string
}

export interface ProfileData {
  id: string
  full_name: string
  role: string
  email: string
  phone: string
  location: string
  company: string
  bio: string
  avatar_url: string
  default_workspace: string
  preferred_language: string
  timezone: string
  timezone_utc: string
  working_hours: string
  email_notifications: boolean
  task_updates: boolean
  approval_requests: boolean
  weekly_digest: boolean
  password_last_changed: string
  two_factor_enabled: boolean
  active_sessions: number
  recent_login: string
  connected_accounts: ConnectedAccount[]
  completion_percentage: number
  completion_items: CompletionItem[]
  recent_activity: ActivityItem[]
  plan: string
  member_since: string
  account_id: string
}

export interface ProfileUpdate {
  full_name?: string
  role?: string
  email?: string
  phone?: string
  location?: string
  company?: string
  bio?: string
  avatar_url?: string
  default_workspace?: string
  preferred_language?: string
  timezone?: string
  timezone_utc?: string
  working_hours?: string
}

export interface NotificationUpdate {
  email_notifications?: boolean
  task_updates?: boolean
  approval_requests?: boolean
  weekly_digest?: boolean
}

export interface ConnectedAccountCreate {
  provider: string
  account_name: string
}

export const useApiProfile = () => {
  const baseURL = useApiBase()

  return {
    getProfile: () => $fetch<ProfileData>('/api/profile', { baseURL }),
    updateProfile: (data: ProfileUpdate) =>
      $fetch<ProfileData>('/api/profile', { method: 'PUT', body: data, baseURL }),
    updateNotifications: (data: NotificationUpdate) =>
      $fetch<ProfileData>('/api/profile/notifications', { method: 'PUT', body: data, baseURL }),
    addConnectedAccount: (data: ConnectedAccountCreate) =>
      $fetch<ProfileData>('/api/profile/connected-accounts', { method: 'POST', body: data, baseURL }),
    deleteConnectedAccount: (provider: string) =>
      $fetch<ProfileData>(`/api/profile/connected-accounts/${encodeURIComponent(provider)}`, { method: 'DELETE', baseURL }),
    toggleChecklist: (itemId: string) =>
      $fetch<ProfileData>(`/api/profile/toggle-checklist/${encodeURIComponent(itemId)}`, { method: 'POST', baseURL }),
    resetProfile: () =>
      $fetch<ProfileData>('/api/profile/reset', { method: 'POST', baseURL })
  }
}
