<script setup lang="ts">
import { FileUp, LoaderCircle, UploadCloud } from '@lucide/vue'

defineProps<{
  uploading: boolean
  status: string
  error: string
}>()

const emit = defineEmits<{
  upload: [file: File]
}>()

const dragActive = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function selectFile(files: FileList | null): void {
  const file = files?.item(0)
  if (file) emit('upload', file)
}

function onInput(event: Event): void {
  if (!(event.currentTarget instanceof HTMLInputElement)) return
  selectFile(event.currentTarget.files)
  event.currentTarget.value = ''
}

function onDrop(event: DragEvent): void {
  dragActive.value = false
  selectFile(event.dataTransfer?.files ?? null)
}
</script>

<template>
  <section
    class="space-y-4"
    aria-labelledby="upload-heading"
  >
    <div
      class="flex min-h-64 flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors"
      :class="dragActive ? 'border-primary bg-primary/5' : 'border-default bg-elevated/50'"
      @dragover.prevent="dragActive = true"
      @dragleave.prevent="dragActive = false"
      @drop.prevent="onDrop"
    >
      <UploadCloud
        class="mb-4 size-10 text-muted"
        aria-hidden="true"
      />
      <h2
        id="upload-heading"
        class="text-base font-semibold text-default"
      >
        Upload source document
      </h2>
      <p class="mt-2 max-w-xs text-sm text-muted">
        PDF, DOCX, TXT, MD, CSV, JSON, or JSONL. Maximum 50 MiB.
      </p>
      <input
        ref="fileInput"
        type="file"
        class="sr-only"
        accept=".pdf,.docx,.txt,.md,.csv,.json,.jsonl"
        :disabled="uploading"
        aria-label="Choose a document to upload"
        @change="onInput"
      >
      <UButton
        class="mt-5"
        :loading="uploading"
        @click="fileInput?.click()"
      >
        <FileUp
          class="size-4"
          aria-hidden="true"
        />
        Choose file
      </UButton>
    </div>

    <div aria-live="polite">
      <UAlert
        v-if="error"
        color="error"
        variant="soft"
        title="Upload failed"
        :description="error"
      />
      <div
        v-else-if="status"
        class="flex items-center gap-2 text-sm text-muted"
      >
        <LoaderCircle
          v-if="uploading"
          class="size-4 animate-spin"
          aria-hidden="true"
        />
        <FileUp
          v-else
          class="size-4 text-primary"
          aria-hidden="true"
        />
        <span>{{ status }}</span>
      </div>
    </div>
  </section>
</template>
