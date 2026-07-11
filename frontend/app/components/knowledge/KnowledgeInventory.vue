<script setup lang="ts">
import { Eye, Files, Trash2 } from '@lucide/vue'
import type { KnowledgeDocument } from '~/types/knowledge'

defineProps<{
  documents: readonly KnowledgeDocument[]
  loading: boolean
  error: string
  deletingId: string | null
}>()

const emit = defineEmits<{
  preview: [document: KnowledgeDocument]
  delete: [document: KnowledgeDocument]
  retry: []
}>()

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KiB', 'MiB'] as const
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}
</script>

<template>
  <section aria-labelledby="inventory-heading">
    <div class="mb-4 flex items-center justify-between gap-4">
      <div>
        <h2
          id="inventory-heading"
          class="text-lg font-semibold text-default"
        >
          Indexed documents
        </h2>
        <p class="mt-1 text-sm text-muted">
          {{ documents.length }} {{ documents.length === 1 ? 'document' : 'documents' }} available to retrieval.
        </p>
      </div>
    </div>

    <UAlert
      v-if="error"
      color="error"
      variant="soft"
      title="Documents unavailable"
      :description="error"
      :actions="[{ label: 'Retry', onClick: () => emit('retry') }]"
    />

    <div
      v-else-if="loading"
      class="space-y-3"
      aria-label="Loading documents"
    >
      <USkeleton
        v-for="index in 4"
        :key="index"
        class="h-14 w-full"
      />
    </div>

    <div
      v-else-if="documents.length === 0"
      class="rounded-lg border border-default bg-elevated/40 px-6 py-12 text-center"
    >
      <Files
        class="mx-auto size-8 text-dimmed"
        aria-hidden="true"
      />
      <h3 class="mt-3 text-sm font-semibold text-default">
        No documents indexed
      </h3>
      <p class="mx-auto mt-1 max-w-sm text-sm text-muted">
        Upload a source file to create searchable vector chunks.
      </p>
    </div>

    <div
      v-else
      class="overflow-x-auto rounded-lg border border-default"
    >
      <table class="w-full min-w-3xl text-left text-sm">
        <thead class="bg-muted/60 text-xs text-muted">
          <tr>
            <th
              scope="col"
              class="px-4 py-3 font-medium"
            >
              Document
            </th>
            <th
              scope="col"
              class="px-4 py-3 font-medium"
            >
              Format
            </th>
            <th
              scope="col"
              class="px-4 py-3 font-medium"
            >
              Size
            </th>
            <th
              scope="col"
              class="px-4 py-3 font-medium"
            >
              Chunks
            </th>
            <th
              scope="col"
              class="px-4 py-3 font-medium"
            >
              Uploaded
            </th>
            <th
              scope="col"
              class="px-4 py-3 text-right font-medium"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-default bg-default">
          <tr
            v-for="document in documents"
            :key="document.id"
            class="hover:bg-muted/40"
          >
            <td class="max-w-72 px-4 py-3">
              <p
                class="truncate font-medium text-default"
                :title="document.title"
              >
                {{ document.title }}
              </p>
              <p
                class="truncate text-xs text-muted"
                :title="document.source_name"
              >
                {{ document.source_name }}
              </p>
            </td>
            <td class="px-4 py-3">
              <UBadge
                color="neutral"
                variant="subtle"
                size="sm"
              >
                {{ document.file_type?.toUpperCase() || 'FILE' }}
              </UBadge>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-muted">
              {{ formatBytes(document.size_bytes) }}
            </td>
            <td class="px-4 py-3 font-mono text-default">
              {{ document.chunk_count }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-muted">
              {{ formatDate(document.created_at) }}
            </td>
            <td class="px-4 py-3">
              <div class="flex justify-end gap-1">
                <UTooltip text="Preview chunks">
                  <UButton
                    color="neutral"
                    variant="ghost"
                    :aria-label="`Preview chunks for ${document.title}`"
                    @click="emit('preview', document)"
                  >
                    <Eye
                      class="size-4"
                      aria-hidden="true"
                    />
                  </UButton>
                </UTooltip>
                <UTooltip text="Delete document">
                  <UButton
                    color="error"
                    variant="ghost"
                    :loading="deletingId === document.id"
                    :aria-label="`Delete ${document.title}`"
                    @click="emit('delete', document)"
                  >
                    <Trash2
                      class="size-4"
                      aria-hidden="true"
                    />
                  </UButton>
                </UTooltip>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
