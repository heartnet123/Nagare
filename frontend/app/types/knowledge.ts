export type KnowledgeDocument = {
  readonly id: string
  readonly title: string
  readonly source_name: string
  readonly content_type: string
  readonly size_bytes: number
  readonly chunk_count: number
  readonly created_at: string
  readonly file_type: string | null
}

export type KnowledgeChunk = {
  readonly id: string
  readonly document_id: string
  readonly chunk_index: number
  readonly text: string
  readonly created_at: string
  readonly page_number: number | null
}

export type KnowledgeChunkPage = {
  readonly items: readonly KnowledgeChunk[]
  readonly total: number
  readonly offset: number
  readonly limit: number
}

export type KnowledgeSearchResult = {
  readonly id: string
  readonly document_id: string
  readonly chunk_index: number
  readonly source: string
  readonly title: string
  readonly page_number: number | null
  readonly file_type: string
  readonly text: string
  readonly distance: number | null
  readonly confidence: number
}

export type KnowledgeDeleteResult = {
  readonly status: string
  readonly message: string
}
