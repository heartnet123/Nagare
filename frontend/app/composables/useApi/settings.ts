import { useApiBase } from './utils'

export interface UserProfile {
  id: string
  username: string
  display_name: string | null
  avatar_url: string | null
  bio: string | null
  email: string | null
  created_at: string
  updated_at: string | null
}

export interface ApiKey {
  id: string
  name: string
  description: string | null
  key_prefix: string
  created_at: string
  expires_at: string | null
  last_used_at: string | null
  is_active: boolean
  key?: string
}

export interface NotificationPreferences {
  email_notifications: boolean
  in_app_notifications: boolean
  agent_alerts: boolean
  weekly_digest: boolean
  security_alerts: boolean
}

export interface ThemeSettings {
  theme: 'light' | 'dark' | 'system'
  accent_color: string | null
  font_size: 'small' | 'medium' | 'large'
}

export interface UserPreferences {
  notifications: NotificationPreferences
  theme: ThemeSettings
  language: string
  timezone: string
}

export const useApiSettings = () => {
  const baseURL = useApiBase()

  return {
    getProfile: () => $fetch<UserProfile>('/api/settings/profile', { baseURL }),
    updateProfile: (data: Partial<UserProfile>) =>
      $fetch<UserProfile>('/api/settings/profile', { method: 'PUT', body: data, baseURL }),
    listApiKeys: () => $fetch<ApiKey[]>('/api/settings/api-keys', { baseURL }),
    createApiKey: (data: { name: string, description?: string, expires_at?: string }) =>
      $fetch<ApiKey>('/api/settings/api-keys', { method: 'POST', body: data, baseURL }),
    revokeApiKey: (id: string) =>
      $fetch<unknown>(`/api/settings/api-keys/${id}`, { method: 'POST', baseURL }),
    deleteApiKey: (id: string) =>
      $fetch<unknown>(`/api/settings/api-keys/${id}`, { method: 'DELETE', baseURL }),
    getNotifications: () => $fetch<NotificationPreferences>('/api/settings/notifications', { baseURL }),
    updateNotifications: (data: Partial<NotificationPreferences>) =>
      $fetch<NotificationPreferences>('/api/settings/notifications', { method: 'PUT', body: data, baseURL }),
    getTheme: () => $fetch<ThemeSettings>('/api/settings/theme', { baseURL }),
    updateTheme: (data: Partial<ThemeSettings>) =>
      $fetch<ThemeSettings>('/api/settings/theme', { method: 'PUT', body: data, baseURL }),
    getPreferences: () => $fetch<UserPreferences>('/api/settings/preferences', { baseURL }),
    updatePreferences: (data: Partial<UserPreferences>) =>
      $fetch<UserPreferences>('/api/settings/preferences', { method: 'PUT', body: data, baseURL })
  }
}
