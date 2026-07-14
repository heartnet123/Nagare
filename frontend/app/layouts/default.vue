<script setup lang="ts">
import { Menu } from '@lucide/vue'

const { sidebarOpen, mobileMenuOpen, toggleSidebar, openMobileMenu, closeMobileMenu } = useAppStore()
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-[var(--ui-bg)] text-[var(--ui-text)] font-sans pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] pl-[env(safe-area-inset-left)] pr-[env(safe-area-inset-right)]">
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
        </div>

        <div class="flex items-center gap-4">
          <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100">
            <div class="w-2 h-2 rounded-full bg-emerald-500" />
            <span class="text-xs font-medium text-emerald-700">
              All Systems Operational
            </span>
          </div>
          <UiThemeToggle />
          <UiUserDropdown />
        </div>
      </header>

      <div class="flex-1 min-h-0 flex flex-col">
        <slot />
      </div>
    </main>
  </div>
</template>
