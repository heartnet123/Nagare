import type { Session, ApiListResponse } from '~/types'
import { useApiBase } from './utils'

export const useApiSessions = () => {
  const baseURL = useApiBase()

  return {
    list: (search?: string) =>
      $fetch<ApiListResponse<Session>>('/api/sessions', { baseURL, query: { search } }),
    listArchived: (search?: string) =>
      $fetch<ApiListResponse<Session>>('/api/sessions/archived', { baseURL, query: { search } }),
    create: (data: { name?: string; model?: string; endpoint_url?: string }) =>
      $fetch<Session>('/api/session', { method: 'POST', body: data, baseURL }),
    get: (sid: string) => $fetch<Session>(`/api/session/${sid}`, { baseURL }),
    update: (sid: string, data: { name?: string; folder?: string; model?: string }) =>
      $fetch<any>(`/api/session/${sid}`, { method: 'PATCH', body: data, baseURL }),
    delete: (sid: string) =>
      $fetch<any>(`/api/session/${sid}`, { method: 'DELETE', baseURL }),
    archive: (sid: string) =>
      $fetch<any>(`/api/session/${sid}/archive`, { method: 'POST', baseURL }),
    unarchive: (sid: string) =>
      $fetch<any>(`/api/session/${sid}/unarchive`, { method: 'POST', baseURL }),
    toggleImportant: (sid: string, important: boolean) =>
      $fetch<any>(`/api/session/${sid}/important`, { method: 'POST', query: { important }, baseURL }),
    getHistory: (sid: string) =>
      $fetch<any[]>(`/api/history/${sid}`, { baseURL }),
    regenerate: (sid: string, model?: string) =>
      $fetch<any>('/api/chat/regenerate', { method: 'POST', body: { session_id: sid, model }, baseURL })
  }
}
