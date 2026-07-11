<script setup lang="ts">
import { Search } from '@lucide/vue'
import type { KnowledgeSearchResult } from '~/types/knowledge'

defineProps<{
  results: readonly KnowledgeSearchResult[]
  searching: boolean
  error: string
}>()

const emit = defineEmits<{
  search: [query: string]
}>()

const query = ref('')

function submit(): void {
  const value = query.value.trim()
  if (value) emit('search', value)
}
</script>

<template>
  <section
    class="border-t border-default pt-8"
    aria-labelledby="search-heading"
  >
    <h2
      id="search-heading"
      class="text-lg font-semibold text-default"
    >
      Test retrieval
    </h2>
    <p class="mt-1 text-sm text-muted">
      Run a semantic query against currently indexed chunks.
    </p>

    <form
      class="mt-4 flex max-w-2xl gap-2"
      role="search"
      @submit.prevent="submit"
    >
      <UInput
        v-model="query"
        class="flex-1"
        placeholder="Search indexed knowledge"
        aria-label="Search indexed knowledge"
      >
        <template #leading>
          <Search
            class="size-4 text-muted"
            aria-hidden="true"
          />
        </template>
      </UInput>
      <UButton
        type="submit"
        label="Search"
        :loading="searching"
        :disabled="!query.trim()"
      />
    </form>

    <UAlert
      v-if="error"
      class="mt-4"
      color="error"
      variant="soft"
      title="Search failed"
      :description="error"
    />

    <ol
      v-else-if="results.length"
      class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <li
        v-for="result in results"
        :key="result.id"
        class="rounded-lg border border-default bg-elevated p-4"
      >
        <div class="flex items-center justify-between gap-3 text-xs text-muted">
          <span
            class="truncate"
            :title="result.source"
          >{{ result.source }}</span>
          <UBadge
            color="primary"
            variant="subtle"
          >
            {{ result.confidence.toFixed(2) }}
          </UBadge>
        </div>
        <p class="mt-3 line-clamp-6 text-sm leading-6 text-default">
          {{ result.text }}
        </p>
        <p
          v-if="result.page_number"
          class="mt-3 text-xs text-muted"
        >
          Page {{ result.page_number }}
        </p>
      </li>
    </ol>
  </section>
</template>
