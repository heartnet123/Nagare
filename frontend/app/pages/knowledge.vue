<script setup lang="ts">
import type {
  KnowledgeChunkPage,
  KnowledgeDocument,
  KnowledgeSearchResult
} from '~/types/knowledge'
import { useApiKnowledge } from '~/composables/useApi/knowledge'

definePageMeta({ layout: 'default' })

const api = useApiKnowledge()
const toast = useToast()
const documents = ref<KnowledgeDocument[]>([])
const documentsLoading = ref(true)
const documentsError = ref('')
const uploading = ref(false)
const uploadStatus = ref('')
const uploadError = ref('')
const deletingId = ref<string | null>(null)
const pendingDelete = ref<KnowledgeDocument | null>(null)
const deleteOpen = ref(false)
const previewOpen = ref(false)
const previewDocument = ref<KnowledgeDocument | null>(null)
const chunkPage = ref<KnowledgeChunkPage | null>(null)
const chunksLoading = ref(false)
const chunksError = ref('')
const searchResults = ref<KnowledgeSearchResult[]>([])
const searching = ref(false)
const searchError = ref('')
const chunkPageSize = 25

function errorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'data' in error) {
    const data = error.data
    if (typeof data === 'object' && data !== null && 'detail' in data && typeof data.detail === 'string') {
      return data.detail
    }
    if (typeof data === 'object' && data !== null && 'error' in data) {
      const nested = data.error
      if (typeof nested === 'object' && nested !== null && 'message' in nested && typeof nested.message === 'string') {
        return nested.message
      }
    }
  }
  return error instanceof Error ? error.message : fallback
}

async function loadDocuments(): Promise<void> {
  documentsLoading.value = true
  documentsError.value = ''
  try {
    documents.value = await api.listDocuments()
  } catch (error) {
    documentsError.value = errorMessage(error, 'Could not load indexed documents.')
  } finally {
    documentsLoading.value = false
  }
}

async function upload(file: File): Promise<void> {
  uploading.value = true
  uploadError.value = ''
  uploadStatus.value = `Indexing ${file.name}`
  try {
    const document = await api.upload(file)
    uploadStatus.value = `${document.title} indexed successfully.`
    await loadDocuments()
    toast.add({ title: 'Document indexed', description: document.source_name, color: 'success' })
  } catch (error) {
    uploadStatus.value = ''
    uploadError.value = errorMessage(error, 'Could not index this document.')
  } finally {
    uploading.value = false
  }
}

function requestDelete(document: KnowledgeDocument): void {
  pendingDelete.value = document
  deleteOpen.value = true
}

async function confirmDelete(): Promise<void> {
  const document = pendingDelete.value
  if (!document) return
  deletingId.value = document.id
  try {
    await api.deleteDocument(document.id)
    deleteOpen.value = false
    pendingDelete.value = null
    await loadDocuments()
    if (previewDocument.value?.id === document.id) previewOpen.value = false
    toast.add({ title: 'Document deleted', description: document.source_name, color: 'success' })
  } catch (error) {
    toast.add({ title: 'Delete failed', description: errorMessage(error, 'Could not delete document.'), color: 'error' })
  } finally {
    deletingId.value = null
  }
}

async function loadChunks(offset: number): Promise<void> {
  const document = previewDocument.value
  if (!document) return
  chunksLoading.value = true
  chunksError.value = ''
  try {
    chunkPage.value = await api.listChunks(document.id, Math.max(0, offset), chunkPageSize)
  } catch (error) {
    chunksError.value = errorMessage(error, 'Could not load document chunks.')
  } finally {
    chunksLoading.value = false
  }
}

async function preview(document: KnowledgeDocument): Promise<void> {
  previewDocument.value = document
  chunkPage.value = null
  previewOpen.value = true
  await loadChunks(0)
}

async function search(query: string): Promise<void> {
  searching.value = true
  searchError.value = ''
  try {
    searchResults.value = await api.search(query, 6)
  } catch (error) {
    searchError.value = errorMessage(error, 'Could not search indexed knowledge.')
  } finally {
    searching.value = false
  }
}

onMounted(loadDocuments)
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Knowledge base"
      description="Index source documents, inspect generated chunks, and manage retrieval content."
    >
      <template #action>
        <UBadge
          color="neutral"
          variant="subtle"
          size="lg"
        >
          {{ documents.length }} indexed
        </UBadge>
      </template>
    </DashboardPageHeader>

    <div class="grid gap-8 lg:grid-cols-[minmax(16rem,20rem)_minmax(0,1fr)]">
      <KnowledgeUploader
        :uploading="uploading"
        :status="uploadStatus"
        :error="uploadError"
        @upload="upload"
      />
      <KnowledgeInventory
        :documents="documents"
        :loading="documentsLoading"
        :error="documentsError"
        :deleting-id="deletingId"
        @preview="preview"
        @delete="requestDelete"
        @retry="loadDocuments"
      />
    </div>

    <KnowledgeSearch
      class="mt-10"
      :results="searchResults"
      :searching="searching"
      :error="searchError"
      @search="search"
    />

    <KnowledgeChunkSlideover
      v-model:open="previewOpen"
      :document="previewDocument"
      :page="chunkPage"
      :loading="chunksLoading"
      :error="chunksError"
      @previous="loadChunks((chunkPage?.offset || 0) - chunkPageSize)"
      @next="loadChunks((chunkPage?.offset || 0) + chunkPageSize)"
      @retry="loadChunks(chunkPage?.offset || 0)"
    />

    <UModal
      v-model:open="deleteOpen"
      title="Delete document"
      :description="pendingDelete ? `Remove ${pendingDelete.title} and all indexed chunks? This cannot be undone.` : ''"
    >
      <template #footer>
        <div class="flex w-full justify-end gap-2">
          <UButton
            color="neutral"
            variant="outline"
            label="Cancel"
            @click="deleteOpen = false"
          />
          <UButton
            color="error"
            label="Delete"
            :loading="deletingId !== null"
            @click="confirmDelete"
          />
        </div>
      </template>
    </UModal>
  </DashboardPageScroll>
</template>
