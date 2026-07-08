<script setup lang="ts">
import { computed } from 'vue'
import { Menu, LayoutGrid, ChevronDown, Sun, Moon, Monitor } from '@lucide/vue'

const { sidebarOpen, mobileMenuOpen, toggleSidebar, openMobileMenu, closeMobileMenu } = useAppStore()
const { chatDrawerOpen, onNavigateToChat } = useSessionStore()

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

const route = useRoute()

// Automatically close the chat drawer when navigating to /chat page
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/chat') {
      onNavigateToChat()
    }
  }
)
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#FAFAFA] dark:bg-stone-950 text-stone-800 dark:text-stone-50 font-sans">
    
    <DashboardSidebar
      :open="sidebarOpen"
      :mobile-open="mobileMenuOpen"
      @close-mobile="closeMobileMenu"
    />
    

    <!-- Sliding Chat Drawer next to Sidebar -->
    <Transition name="slide">
      <div
        v-if="chatDrawerOpen"
        class="border-r border-stone-200 dark:border-stone-700 bg-white dark:bg-stone-950 flex flex-col shrink-0 relative z-30 overflow-hidden"
      >
        <div class="w-[440px] h-full flex flex-col">
          <ChatChatView :is-in-drawer="true" />
        </div>
      </div>
    </Transition>

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

          <button class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-stone-200 bg-white shadow-sm text-sm font-medium text-stone-700 hover:bg-stone-50 transition-colors">
            <LayoutGrid
              :size="16"
              :stroke-width="1.5"
            />
            Default Workspace
            <ChevronDown
              :size="14"
              :stroke-width="1.5"
              class="ml-1 text-stone-400"
            />
          </button>
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
          <div class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-medium text-sm shadow-sm">
            N
          </div>
        </div>
      </header>

      <div class="flex-1 min-h-0 flex flex-col">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  width: 0px;
  opacity: 0;
}
</style>
