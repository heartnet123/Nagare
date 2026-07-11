import { useApiBase } from './utils'
import type {
  KnowledgeChunkPage,
  KnowledgeDeleteResult,
  KnowledgeDocument,
  KnowledgeSearchResult
} from '~/types/knowledge'

export const useApiKnowledge = () => {
  const baseURL = useApiBase()
  const csrfToken = useCookie<string | null>('csrf_token')

  const mutationHeaders = () => csrfToken.value
    ? { 'X-CSRF-Token': csrfToken.value }
    : undefined

  return {
    upload: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return $fetch<KnowledgeDocument>('/api/knowledge/upload', {
        method: 'POST',
        body: formData,
        baseURL,
        credentials: 'include',
        headers: mutationHeaders()
      })
    },
    listDocuments: () =>
      $fetch<KnowledgeDocument[]>('/api/knowledge/documents', {
        baseURL,
        credentials: 'include'
      }),
    listChunks: (docId: string, offset = 0, limit = 100) =>
      $fetch<KnowledgeChunkPage>(`/api/knowledge/document/${encodeURIComponent(docId)}/chunks`, {
        baseURL,
        credentials: 'include',
        query: { offset, limit }
      }),
    deleteDocument: (docId: string) =>
      $fetch<KnowledgeDeleteResult>(`/api/knowledge/document/${encodeURIComponent(docId)}`, {
        method: 'DELETE',
        baseURL,
        credentials: 'include',
        headers: mutationHeaders()
      }),
    search: (query: string, limit?: number) =>
      $fetch<KnowledgeSearchResult[]>('/api/knowledge/search', {
        baseURL,
        credentials: 'include',
        query: { q: query, limit }
      })
  }
}
