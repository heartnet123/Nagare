<script setup lang="ts">
import { Sun, Moon } from '@lucide/vue'

const colorMode = useColorMode()

const isDark = computed({
  get() {
    return colorMode.value === 'dark'
  },
  set() {
    colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
  }
})
</script>

<template>
  <UButton
    color="neutral"
    variant="ghost"
    size="md"
    aria-label="Toggle theme"
    @click="isDark = !isDark"
  >
    <Moon
      v-if="isDark"
      class="size-5"
    />
    <Sun
      v-else
      class="size-5"
    />
  </UButton>
</template>
