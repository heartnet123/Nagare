<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import {
  SquarePen,
  Waves,
  X,
  Command,
  MessageSquare,
  MoreVertical
} from '@lucide/vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { navItems } from '~/utils/nav'
import type { NavItem } from '~/types'

defineProps<{
  open: boolean
  mobileOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'closeMobile'): void
}>()

const route = useRoute()
const showAllSessions = ref(false)
const { sessions, recentSessions, loadSessions } = useSessionStore()
const visibleLimit = ref(20)
const sidebarSessions = computed(() => showAllSessions.value ? sessions.value.slice(0, visibleLimit.value) : recentSessions.value)

// Auto-load sessions once
if (import.meta.client && recentSessions.value.length === 0) {
  loadSessions()
}

// Session manipulation state
const editingSessionId = ref<string | null>(null)
const editingName = ref('')
const renameInput = ref<HTMLInputElement[] | null>(null)
const api = useApi()

const isActive = (item: NavItem) => {
  const pathname = route.path
  if (item.matchRoutes?.length) {
    return item.matchRoutes.some(r => r === '/' ? pathname === '/' : pathname.startsWith(r))
  }
  return item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
}

const isNewChatLinkActive = computed(() => {
  return route.path === '/'
})

const isRecentChatActive = (sessionId: string) => {
  if (route.path.startsWith('/session/')) {
    return route.params.id === sessionId
  }
  return false
}

const handleNewChatClick = () => {
  emit('closeMobile')
}

const handleRecentChatClick = () => {
  emit('closeMobile')
}

// Session manipulation functions
const startRename = (sid: string, name: string) => {
  editingSessionId.value = sid
  editingName.value = name
  nextTick(() => {
    if (renameInput.value && renameInput.value[0]) {
      renameInput.value[0].focus()
      renameInput.value[0].select()
    }
  })
}

const saveRename = async (sid: string) => {
  if (!editingSessionId.value) return
  const finalName = editingName.value.trim()
  editingSessionId.value = null
  if (!finalName) return

  try {
    await api.sessions.update(sid, { name: finalName })
    await loadSessions()
  } catch (error) {
    console.error('Failed to rename session:', error)
  }
}

const cancelRename = () => {
  editingSessionId.value = null
  editingName.value = ''
}

const deleteSession = async (sid: string) => {
  if (!confirm('Are you sure you want to permanently delete this conversation?')) return
  try {
    await api.sessions.delete(sid)
    await loadSessions()
  } catch (error) {
    console.error('Failed to delete session:', error)
  }
}

const getSessionMenuItems = (session: { id: string, name: string }): DropdownMenuItem[][] => {
  return [
    [
      {
        label: 'Rename',
        icon: 'i-lucide-pencil',
        onSelect: () => startRename(session.id, session.name)
      },
      {
        label: 'Delete',
        icon: 'i-lucide-trash-2',
        color: 'error',
        onSelect: () => deleteSession(session.id)
      }
    ]
  ]
}
</script>

<template>
  <div class="h-dvh">
    <!-- Mobile Backdrop -->
    <Transition name="fade">
      <div
        v-if="mobileOpen"
        class="fixed inset-0 z-40 bg-stone-900/20 md:hidden"
        @click="emit('closeMobile')"
      />
    </Transition>

    <nav
      aria-label="Main Navigation"
      class="fixed md:static inset-y-0 left-0 z-50 h-dvh flex flex-col bg-white dark:bg-stone-900 border-r border-slate-200/80 dark:border-stone-800 transition-all duration-300 ease-in-out overflow-hidden shrink-0"
      :class="[
        open ? 'w-[260px]' : 'w-0 !border-r-0',
        mobileOpen ? 'translate-x-0 !w-[260px]' : '-translate-x-full md:translate-x-0'
      ]"
    >
      <div
        class="w-[260px] min-w-[260px] h-full flex flex-col transition-transform duration-300 ease-in-out"
        :class="[!open && 'md:-translate-x-full']"
      >
        <div class="flex items-center justify-between p-6 w-full shrink-0">
          <NuxtLink
            to="/"
            class="flex items-center gap-3 overflow-hidden"
          >
            <div class="flex items-center justify-center w-8 h-8 text-emerald-600 dark:text-emerald-500 shrink-0">
              <Waves
                :size="28"
                :stroke-width="2"
              />
            </div>
            <div class="flex flex-col">
              <span class="font-sans font-bold tracking-tight text-stone-900 dark:text-stone-100 leading-tight">
                NAGARE OS
              </span>
              <span class="text-[10px] font-medium text-stone-500 dark:text-stone-400 uppercase tracking-widest leading-tight">
                AI Operating System
              </span>
            </div>
          </NuxtLink>
          <button
            class="md:hidden p-1 text-stone-400 dark:text-stone-500 hover:text-stone-800 dark:hover:text-stone-200"
            aria-label="Close menu"
            @click="emit('closeMobile')"
          >
            <X
              :size="20"
              :stroke-width="1.5"
            />
          </button>
        </div>

        <div class="flex-1 overflow-y-auto py-3 space-y-5 hide-scrollbar px-3">
          <!-- Primary Navigation matching image -->
          <div class="space-y-1">
            <NuxtLink
              v-for="item in navItems"
              :key="item.href"
              :to="item.href"
              class="flex items-center w-full px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors group"
              :class="[
                isActive(item)
                  ? 'bg-[#ebf3ff] text-[#2563eb] dark:bg-blue-950/40 dark:text-blue-400 font-medium'
                  : 'text-slate-600 dark:text-stone-400 hover:bg-slate-100/80 dark:hover:bg-stone-800/40 hover:text-slate-900 dark:hover:text-stone-200'
              ]"
              @click="emit('closeMobile')"
            >
              <component
                :is="item.icon"
                :size="19"
                :stroke-width="1.75"
                class="shrink-0 transition-colors"
                :class="[
                  isActive(item)
                    ? 'text-[#2563eb] dark:text-blue-400'
                    : 'text-slate-500 dark:text-stone-400 group-hover:text-slate-800 dark:group-hover:text-stone-200'
                ]"
              />
              <span class="ml-3 truncate">{{ item.label }}</span>
              <span
                v-if="item.badge"
                class="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full"
                :class="[
                  isActive(item)
                    ? 'bg-[#dbeafe] text-[#2563eb] dark:bg-blue-900/60 dark:text-blue-300'
                    : 'bg-slate-100 text-slate-600 dark:bg-stone-800 dark:text-stone-400'
                ]"
              >
                {{ item.badge }}
              </span>
            </NuxtLink>
          </div>

          <!-- Divider -->
          <div class="pt-2 border-t border-slate-200/60 dark:border-stone-800" />

          <!-- New Chat Link -->
          <div class="space-y-1">
            <NuxtLink
              to="/"
              class="flex items-center justify-between w-full px-3 py-2 rounded-xl text-stone-600 dark:text-stone-400 hover:bg-stone-200/50 dark:hover:bg-stone-800/30 hover:text-stone-800 dark:hover:text-stone-200"
              :class="[
                isNewChatLinkActive ? 'bg-stone-100 dark:bg-stone-800 text-stone-900 dark:text-stone-100' : ''
              ]"
              @click="handleNewChatClick"
            >
              <div class="flex items-center">
                <SquarePen
                  :size="17"
                  :stroke-width="1.5"
                  class="shrink-0"
                />
                <span class="ml-3 text-xs font-medium">New Chat</span>
              </div>
              <div class="flex items-center gap-0.5 px-1.5 py-0.5 rounded-md bg-stone-200 dark:bg-stone-800 text-[10px] text-stone-500 dark:text-stone-400 font-medium">
                <Command :size="10" /> K
              </div>
            </NuxtLink>
          </div>

          <!-- Recent Chats (visible when active chats exist) -->
          <div
            v-if="recentSessions.length > 0"
            class="space-y-1"
          >
            <div class="px-3 mb-2 flex items-center justify-between gap-2 text-[11px] font-semibold tracking-wider text-stone-400 dark:text-stone-500 uppercase">
              <span>Conversations</span>
              <button
                v-if="sessions.length > recentSessions.length"
                class="normal-case tracking-normal text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 font-semibold"
                @click="showAllSessions = !showAllSessions"
              >
                {{ showAllSessions ? 'Show 5' : 'See all' }}
              </button>
            </div>
            <div class="space-y-0.5">
              <div
                v-for="s in sidebarSessions"
                :key="s.id"
                class="group/item"
              >
                <!-- Normal view -->
                <div
                  v-if="editingSessionId !== s.id"
                  class="flex items-center w-full px-3 py-2 rounded-xl text-stone-500 dark:text-stone-400 hover:bg-stone-200/50 dark:hover:bg-stone-800/30 hover:text-stone-800 dark:hover:text-stone-200"
                  :class="[
                    isRecentChatActive(s.id)
                      ? 'bg-white dark:bg-stone-800 shadow-sm border border-stone-200/60 dark:border-stone-700 text-stone-900 dark:text-stone-100'
                      : ''
                  ]"
                >
                  <NuxtLink
                    :to="`/session/${s.id}`"
                    class="flex items-center flex-1 min-w-0"
                    @click="handleRecentChatClick"
                  >
                    <MessageSquare
                      :size="15"
                      :stroke-width="1.5"
                      class="shrink-0 text-stone-400 mr-2"
                    />
                    <span class="text-xs font-medium truncate flex-1 leading-none">{{ s.name }}</span>
                  </NuxtLink>
                  <UDropdownMenu
                    :items="getSessionMenuItems(s)"
                    :ui="{ content: 'w-40' }"
                    class="opacity-0 group-hover/item:opacity-100 transition-opacity"
                  >
                    <UButton
                      color="neutral"
                      variant="ghost"
                      class="p-2.5 -m-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center"
                      aria-label="Session actions"
                      @click.stop
                    >
                      <MoreVertical
                        :size="14"
                        :stroke-width="1.5"
                        class="text-stone-400"
                      />
                    </UButton>
                  </UDropdownMenu>
                </div>

                <!-- Edit view -->
                <div
                  v-else
                  class="flex items-center w-full px-3 py-2 rounded-xl bg-white dark:bg-stone-800 shadow-sm border border-stone-200/60 dark:border-stone-700"
                >
                  <MessageSquare
                    :size="15"
                    :stroke-width="1.5"
                    class="shrink-0 text-stone-400 mr-2"
                  />
                  <input
                    ref="renameInput"
                    v-model="editingName"
                    type="text"
                    class="flex-1 text-xs font-medium bg-transparent border-none outline-none text-stone-900 dark:text-stone-100"
                    @keydown.enter="saveRename(s.id)"
                    @keydown.escape="cancelRename"
                    @blur="saveRename(s.id)"
                  >
                </div>
              </div>
              <!-- Load more button if there are more sessions remaining -->
              <button
                v-if="showAllSessions && sessions.length > visibleLimit"
                class="w-full mt-2 py-1.5 text-xs text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 hover:bg-stone-200/30 dark:hover:bg-stone-800/20 rounded-xl font-semibold text-center"
                @click="visibleLimit += 20"
              >
                Load more ({{ sessions.length - visibleLimit }} remaining)
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
