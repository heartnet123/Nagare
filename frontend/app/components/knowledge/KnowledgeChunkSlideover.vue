<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileSearch } from '@lucide/vue'
import type { KnowledgeChunkPage, KnowledgeDocument } from '~/types/knowledge'

const open = defineModel<boolean>('open', { required: true })

const props = defineProps<{
  document: KnowledgeDocument | null
  page: KnowledgeChunkPage | null
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  previous: []
  next: []
  retry: []
}>()

const rangeLabel = computed(() => {
  if (!props.page || props.page.total === 0) return 'No chunks'
  const start = props.page.offset + 1
  const end = Math.min(props.page.offset + props.page.items.length, props.page.total)
  return `${start}-${end} of ${props.page.total}`
})

const canGoBack = computed(() => Boolean(props.page && props.page.offset > 0))
const canGoForward = computed(() => Boolean(
  props.page && props.page.offset + props.page.items.length < props.page.total
))
</script>

<template>
  <USlideover
    v-model:open="open"
    :title="document?.title || 'Document chunks'"
    :description="document ? `${document.chunk_count} indexed chunks from ${document.source_name}` : undefined"
  >
    <template #body>
      <UAlert
        v-if="error"
        color="error"
        variant="soft"
        title="Chunks unavailable"
        :description="error"
        :actions="[{ label: 'Retry', onClick: () => emit('retry') }]"
      />

      <div
        v-else-if="loading"
        class="space-y-4"
        aria-label="Loading chunks"
      >
        <USkeleton
          v-for="index in 5"
          :key="index"
          class="h-28 w-full"
        />
      </div>

      <div
        v-else-if="page?.items.length === 0"
        class="py-12 text-center"
      >
        <FileSearch
          class="mx-auto size-8 text-dimmed"
          aria-hidden="true"
        />
        <p class="mt-3 text-sm text-muted">
          No chunks found for this document.
        </p>
      </div>

      <ol
        v-else
        class="divide-y divide-default"
      >
        <li
          v-for="chunk in page?.items"
          :key="chunk.id"
          class="py-5 first:pt-0"
        >
          <div class="mb-2 flex items-center justify-between gap-3 text-xs text-muted">
            <span class="font-mono">Chunk {{ chunk.chunk_index + 1 }}</span>
            <span v-if="chunk.page_number">Page {{ chunk.page_number }}</span>
          </div>
          <p class="whitespace-pre-wrap break-words text-sm leading-6 text-default">
            {{ chunk.text }}
          </p>
        </li>
      </ol>
    </template>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-3">
        <span class="text-sm text-muted">{{ rangeLabel }}</span>
        <div class="flex gap-2">
          <UButton
            color="neutral"
            variant="outline"
            :disabled="!canGoBack || loading"
            @click="emit('previous')"
          >
            <ChevronLeft
              class="size-4"
              aria-hidden="true"
            />
            Previous
          </UButton>
          <UButton
            color="neutral"
            variant="outline"
            :disabled="!canGoForward || loading"
            @click="emit('next')"
          >
            Next
            <ChevronRight
              class="size-4"
              aria-hidden="true"
            />
          </UButton>
        </div>
      </div>
    </template>
  </USlideover>
</template>
