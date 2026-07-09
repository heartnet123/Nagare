<script setup lang="ts">
import { computed } from 'vue'
import { Menu, Sun, Moon, Monitor } from '@lucide/vue'

const { sidebarOpen, mobileMenuOpen, toggleSidebar, openMobileMenu, closeMobileMenu } = useAppStore()

const colorMode = useColorMode()

const themeIcon = computed(() => ({
  light: Sun,
  dark: Moon,
  system: Monitor
}[colorMode.preference] ?? Sun))

function cycleTheme() {
  const order = ['light', 'dark', 'system'] as const
  const idx = order.indexOf(colorMode.preference as typeof order[number])
  colorMode.preference = order[(idx + 1) % 3] as string
}
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#FAFAFA] dark:bg-stone-950 text-stone-800 dark:text-stone-50 font-sans">
    
    <DashboardSidebar
      :open="sidebarOpen"
      :mobile-open="mobileMenuOpen"
      @close-mobile="closeMobileMenu"
    />

    <main class="flex-1 flex flex-col min-w-0 overflow-hidden relative">
      <header class="flex items-center justify-between px-6 py-4 shrink-0">
        <div class="flex items-center gap-4">
          <button
            class="p-1.5 -ml-2 rounded-lg text-stone-500 hover:bg-stone-200 md:hidden"
            aria-label="Open menu"
            @click="openMobileMenu"
          >
            <Menu
              :size="20"
              :stroke-width="1.5"
            />
          </button>
          <button
            class="hidden md:block p-1.5 -ml-2 rounded-lg text-stone-500 hover:bg-stone-200"
            aria-label="Toggle sidebar"
            @click="toggleSidebar"
          >
            <Menu
              :size="20"
              :stroke-width="1.5"
            />
          </button>

          <WorkspaceDropdown />
        </div>

        <div class="flex items-center gap-4">
          <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100">
            <div class="w-2 h-2 rounded-full bg-emerald-500" />
            <span class="text-xs font-medium text-emerald-700">
              All Systems Operational
            </span>
          </div>
          <button
            class="p-2 rounded-full bg-white dark:bg-stone-800 border border-stone-200 dark:border-stone-700 text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-50 hover:bg-stone-50 dark:hover:bg-stone-700 shadow-sm transition-colors"
            :aria-label="`Theme: ${colorMode.preference}`"
            @click="cycleTheme"
          >
            <component
              :is="themeIcon"
              :size="18"
              :stroke-width="1.5"
            />
          </button>
          <UiUserDropdown />
        </div>
      </header>

      <div class="flex-1 min-h-0 flex flex-col">
        <slot />
      </div>
    </main>
  </div>
</template>
