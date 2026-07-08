import { useApiBase } from './utils'

export const useApiKnowledge = () => {
  const baseURL = useApiBase()

  return {
    upload: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return $fetch<any>('/api/knowledge/upload', {
        method: 'POST',
        body: formData,
        baseURL
      })
    },
    listDocuments: () =>
      $fetch<any[]>('/api/knowledge/documents', { baseURL }),
    deleteDocument: (docId: string) =>
      $fetch<any>(`/api/knowledge/document/${docId}`, { method: 'DELETE', baseURL }),
    search: (query: string, limit?: number) =>
      $fetch<any[]>('/api/knowledge/search', { baseURL, query: { q: query, limit } })
  }
}
