<script setup lang="ts">
import { Save, Loader2 } from '@lucide/vue'

const api = useApi()
const colorMode = useColorMode()
const loading = ref(true)
const saving = ref(false)
const toast = useToast()

const theme = reactive({
  theme: 'system' as 'light' | 'dark' | 'system',
  accent_color: null as string | null,
  font_size: 'medium' as 'small' | 'medium' | 'large'
})

const themeOptions = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' }
]

const fontSizeOptions = [
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large' }
]

const accentColors = [
  { value: null, label: 'Default', color: '#6366f1' },
  { value: '#ef4444', label: 'Red', color: '#ef4444' },
  { value: '#f97316', label: 'Orange', color: '#f97316' },
  { value: '#eab308', label: 'Yellow', color: '#eab308' },
  { value: '#22c55e', label: 'Green', color: '#22c55e' },
  { value: '#06b6d4', label: 'Cyan', color: '#06b6d4' },
  { value: '#8b5cf6', label: 'Purple', color: '#8b5cf6' }
]

async function loadTheme() {
  loading.value = true
  try {
    const data = await api.settings.getTheme()
    Object.assign(theme, data)
    colorMode.preference = theme.theme
  } catch {
    toast.add({ title: 'Failed to load theme settings', color: 'error' })
  } finally {
    loading.value = false
  }
}

async function saveTheme() {
  saving.value = true
  try {
    await api.settings.updateTheme({ ...theme })
    colorMode.preference = theme.theme
    toast.add({ title: 'Theme settings saved', color: 'success' })
  } catch {
    toast.add({ title: 'Failed to save theme settings', color: 'error' })
  } finally {
    saving.value = false
  }
}

onMounted(loadTheme)
</script>

<template>
  <UCard>
    <div
      v-if="loading"
      class="flex justify-center py-8"
    >
      <Loader2 class="w-6 h-6 animate-spin text-muted" />
    </div>
    <div
      v-else
      class="space-y-6"
    >
      <!-- Theme Mode -->
      <div>
        <label class="text-sm font-medium mb-3 block">Theme Mode</label>
        <URadioGroup
          v-model="theme.theme"
          :options="themeOptions"
        />
      </div>

      <!-- Font Size -->
      <div>
        <label class="text-sm font-medium mb-3 block">Font Size</label>
        <URadioGroup
          v-model="theme.font_size"
          :options="fontSizeOptions"
        />
      </div>

      <!-- Accent Color -->
      <div>
        <label class="text-sm font-medium mb-3 block">Accent Color</label>
        <div class="flex gap-3">
          <button
            v-for="color in accentColors"
            :key="color.value ?? 'default'"
            :class="[
              'w-8 h-8 rounded-full border-2 transition-all',
              theme.accent_color === color.value ? 'border-foreground scale-110' : 'border-transparent'
            ]"
            :style="{ backgroundColor: color.color }"
            :title="color.label"
            @click="theme.accent_color = color.value"
          />
        </div>
      </div>

      <div class="flex justify-end">
        <UButton
          :loading="saving"
          @click="saveTheme"
        >
          <Save class="w-4 h-4 mr-2" />
          Save Theme
        </UButton>
      </div>
    </div>
  </UCard>
</template>
