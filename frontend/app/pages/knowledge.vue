<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  UploadCloud,
  FileText,
  Trash2,
  Search,
  Sparkles,
  Database,
  ArrowRight,
  FileCode,
  CheckCircle2,
  XCircle,
  Loader2,
  FileSpreadsheet,
  File
} from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

const api = useApi()

// Ingest/Upload states
const dragOver = ref(false)
const uploading = ref(false)
const uploadProgressText = ref('')
const uploadError = ref('')

// Documents List states
const documents = ref<any[]>([])
const loadingDocs = ref(false)

// Query Search Preview states
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<any[]>([])
const searchError = ref('')

// Load documents from backend
const loadDocuments = async () => {
  loadingDocs.value = true
  try {
    documents.value = await api.knowledge.listDocuments()
  } catch (err: any) {
    console.error('Failed to list documents:', err)
  } finally {
    loadingDocs.value = false
  }
}

// Format file size
const formatBytes = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Format date string
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

// Upload file
const uploadFile = async (file: File) => {
  uploading.value = true
  uploadError.value = ''
  uploadProgressText.value = `Uploading "${file.name}"...`
  try {
    await api.knowledge.upload(file)
    uploadProgressText.value = `Successfully indexed "${file.name}"!`
    setTimeout(() => {
      uploadProgressText.value = ''
      uploading.value = false
    }, 2000)
    await loadDocuments()
  } catch (err: any) {
    uploadError.value = err.data?.detail || err.message || 'Indexing failed'
    uploading.value = false
  }
}

// Drag & Drop event handlers
const handleDrop = (e: DragEvent) => {
  dragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files[0]) {
    uploadFile(files[0])
  }
}

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files[0]) {
    uploadFile(files[0])
  }
}

// Delete document
const deleteDoc = async (id: string, title: string) => {
  if (!confirm(`Are you sure you want to permanently delete "${title}"? This cannot be undone.`)) return
  try {
    await api.knowledge.deleteDocument(id)
    await loadDocuments()
  } catch (err: any) {
    alert(`Deletion failed: ${err.message}`)
  }
}

// Semantic Search test
const runSearch = async () => {
  const q = searchQuery.value.trim()
  if (!q) return
  searching.value = true
  searchError.value = ''
  searchResults.value = []
  try {
    searchResults.value = await api.knowledge.search(q, 3)
  } catch (err: any) {
    searchError.value = err.data?.detail || err.message || 'Query search failed'
  } finally {
    searching.value = false
  }
}

// Dynamic File Icon based on type
const getFileIcon = (fileType: string) => {
  const type = (fileType || '').toLowerCase()
  if (type === 'pdf') return FileText
  if (type === 'docx') return FileText
  if (type === 'csv') return FileSpreadsheet
  if (type === 'json' || type === 'jsonl') return FileCode
  return File
}

onMounted(() => {
  loadDocuments()
})
</script>

<template>
  <div class="flex-1 overflow-y-auto px-6 pb-12 hide-scrollbar">
    <div class="max-w-6xl mx-auto w-full py-8">
      
      <!-- Title Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 class="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
            RAG Knowledge Base
          </h1>
          <p class="text-stone-500 dark:text-stone-400 text-sm mt-1">
            Upload source files to construct vectors. Connect your documents to let the agent retrieve contextual evidence.
          </p>
        </div>
        <div class="flex items-center gap-3 bg-stone-100 dark:bg-stone-900 border border-stone-200 dark:border-stone-850 px-4 py-2 rounded-xl text-stone-600 dark:text-stone-300 text-xs font-semibold">
          <Database :size="14" class="text-blue-500" />
          {{ documents.length }} Documents Ingested
        </div>
      </div>

      <!-- Ingest Grid Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <!-- Left: Upload Area -->
        <div class="lg:col-span-1 flex flex-col gap-6">
          <div
            class="relative border-2 border-dashed rounded-2xl p-8 text-center flex flex-col items-center justify-center transition-all duration-300 min-h-[300px]"
            :class="[
              dragOver
                ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-950/20'
                : 'border-stone-300 dark:border-stone-800 hover:border-blue-400 dark:hover:border-blue-800/80 bg-white dark:bg-stone-900/40'
            ]"
            @dragover.prevent="dragOver = true"
            @dragleave.prevent="dragOver = false"
            @drop.prevent="handleDrop"
          >
            <!-- File Input trigger -->
            <input
              id="file-selector"
              type="file"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".pdf,.docx,.txt,.md,.csv,.json"
              @change="handleFileSelect"
            />

            <UploadCloud :size="48" class="text-stone-400 mb-4 animate-bounce" />
            <h3 class="text-sm font-semibold text-stone-800 dark:text-stone-200 mb-1">
              Drag & drop document here
            </h3>
            <p class="text-xs text-stone-400 dark:text-stone-500 max-w-[200px] mb-4">
              Supports PDF, DOCX, TXT, MD, CSV, or JSON (Max 50MB)
            </p>

            <button
              class="relative z-10 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-medium shadow-sm transition-colors"
            >
              Browse Files
            </button>
          </div>

          <!-- Loading & Progress indicator -->
          <div v-if="uploading || uploadError" class="p-4 rounded-xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900 shadow-sm text-xs transition-all">
            <div v-if="uploading" class="flex items-center gap-2 text-stone-600 dark:text-stone-400">
              <Loader2 :size="16" class="animate-spin text-blue-500" />
              <span>{{ uploadProgressText }}</span>
            </div>
            <div v-if="uploadError" class="flex gap-2 text-red-600 dark:text-red-400">
              <XCircle :size="16" class="shrink-0 mt-0.5" />
              <div>
                <span class="font-bold">Parsing Error</span>
                <p class="mt-0.5">{{ uploadError }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Documents Table List -->
        <div class="lg:col-span-2 flex flex-col gap-6">
          <div class="rounded-2xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/60 overflow-hidden shadow-sm flex-1 flex flex-col">
            <div class="px-6 py-4 border-b border-stone-200 dark:border-stone-800 flex justify-between items-center bg-stone-50/50 dark:bg-stone-900/30">
              <h2 class="text-sm font-semibold text-stone-800 dark:text-stone-200">
                Indexed Sources
              </h2>
            </div>

            <!-- Documents Table -->
            <div class="flex-1 overflow-x-auto min-h-[300px]">
              <div v-if="loadingDocs" class="flex flex-col items-center justify-center py-20 text-stone-400">
                <Loader2 :size="32" class="animate-spin mb-2" />
                <span>Loading Indexed Documents...</span>
              </div>
              <div v-else-if="documents.length === 0" class="flex flex-col items-center justify-center py-20 text-stone-400 text-center px-4">
                <FileText :size="40" class="text-stone-300 dark:text-stone-700 mb-3" />
                <h3 class="text-sm font-semibold text-stone-800 dark:text-stone-300 mb-1">No documents found</h3>
                <p class="text-xs text-stone-400 dark:text-stone-500 max-w-xs">Upload files on the left to start embedding chunks in the database.</p>
              </div>
              <table v-else class="w-full text-left border-collapse text-xs">
                <thead>
                  <tr class="bg-stone-100/50 dark:bg-stone-900/40 text-stone-500 dark:text-stone-400 border-b border-stone-200 dark:border-stone-800 font-semibold">
                    <th class="px-6 py-3">Document Title</th>
                    <th class="px-4 py-3">Format</th>
                    <th class="px-4 py-3">Size</th>
                    <th class="px-4 py-3">Vector Chunks</th>
                    <th class="px-4 py-3">Uploaded</th>
                    <th class="px-6 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-stone-200 dark:divide-stone-800 text-stone-700 dark:text-stone-300 font-medium">
                  <tr v-for="doc in documents" :key="doc.id" class="hover:bg-stone-50/50 dark:hover:bg-stone-900/20">
                    <td class="px-6 py-4 flex items-center gap-3">
                      <component :is="getFileIcon(doc.file_type)" :size="16" class="text-blue-500 shrink-0" />
                      <span class="font-semibold truncate max-w-[200px]" :title="doc.title">{{ doc.title }}</span>
                    </td>
                    <td class="px-4 py-4">
                      <span class="uppercase px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-900">
                        {{ doc.file_type || 'TXT' }}
                      </span>
                    </td>
                    <td class="px-4 py-4 text-stone-400">{{ formatBytes(doc.size_bytes) }}</td>
                    <td class="px-4 py-4 font-mono font-bold">{{ doc.chunk_count }}</td>
                    <td class="px-4 py-4 text-stone-400">{{ formatDate(doc.created_at) }}</td>
                    <td class="px-6 py-4 text-right">
                      <button
                        class="p-1.5 rounded-lg hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/40 text-stone-450 dark:text-stone-500 transition-colors"
                        title="Delete Document"
                        @click="deleteDoc(doc.id, doc.title)"
                      >
                        <Trash2 :size="14" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Testing Semantic Search Preview Section -->
      <div class="mt-12 border-t border-stone-200 dark:border-stone-800 pt-10">
        <h2 class="text-lg font-bold text-stone-800 dark:text-stone-100 mb-2 flex items-center gap-2">
          <Sparkles :size="18" class="text-blue-500" />
          Semantic Retrieval Playground
        </h2>
        <p class="text-stone-500 dark:text-stone-400 text-xs mb-6">
          Execute search queries against vector database embeddings directly. Test how relevance ranking and confidence scoring weights your context.
        </p>

        <!-- Search Input Bar -->
        <div class="relative flex items-center max-w-2xl bg-white dark:bg-stone-900 border border-stone-200 dark:border-stone-850 rounded-2xl px-4 py-2 shadow-sm focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:border-blue-500 transition-shadow">
          <Search :size="18" class="text-stone-400 shrink-0 mr-3" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Type a testing query and press Enter..."
            class="w-full bg-transparent border-0 outline-none text-sm text-stone-700 dark:text-stone-200 placeholder-stone-400"
            @keydown.enter="runSearch"
          />
          <button
            :disabled="searching || !searchQuery.trim()"
            class="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            @click="runSearch"
          >
            <Loader2 v-if="searching" :size="14" class="animate-spin mr-1 inline" />
            Query
          </button>
        </div>

        <!-- Search Results Grid -->
        <div v-if="searchResults.length > 0" class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div
            v-for="(res, idx) in searchResults"
            :key="res.id"
            class="p-5 rounded-2xl border border-stone-200 dark:border-stone-800 bg-white dark:bg-stone-900/40 shadow-sm hover:border-blue-500/40 transition-colors flex flex-col"
          >
            <!-- Chunk Header -->
            <div class="flex items-center justify-between gap-2 mb-3 border-b border-stone-100 dark:border-stone-800 pb-2">
              <span class="text-[10px] uppercase font-bold text-stone-400 tracking-wider">
                Result {{ idx + 1 }}
              </span>
              <div class="flex items-center gap-1.5">
                <span class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-100 dark:border-emerald-900/60 px-1.5 py-0.5 rounded">
                  Score: {{ res.confidence }}
                </span>
              </div>
            </div>

            <!-- Chunk Content Text -->
            <p class="text-xs leading-relaxed text-stone-600 dark:text-stone-300 italic flex-1 mb-4">
              "{{ res.text }}"
            </p>

            <!-- Citation Metadata -->
            <div class="flex items-center justify-between text-[10px] text-stone-400 dark:text-stone-500 font-mono tracking-wide">
              <span class="truncate max-w-[150px] font-semibold flex items-center gap-1" :title="res.source">
                <FileText :size="11" />
                {{ res.source }}
              </span>
              <span v-if="res.page_number" class="bg-stone-100 dark:bg-stone-800/80 px-1 rounded text-stone-500">
                Page {{ res.page_number }}
              </span>
            </div>
          </div>
        </div>

        <div v-else-if="searchError" class="mt-4 text-xs text-red-500 font-medium">
          {{ searchError }}
        </div>
      </div>

    </div>
  </div>
</template>
