<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import {
  SquarePen,
  Waves,
  X,
  ArrowRight,
  Command,
  MessageSquare,
  MoreVertical,
  Pencil,
  Trash2
} from '@lucide/vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { navGroups } from '~/utils/nav'

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
const sidebarSessions = computed(() => showAllSessions.value ? sessions.value : recentSessions.value)

// Auto-load sessions once
if (import.meta.client && recentSessions.value.length === 0) {
  loadSessions()
}

// Session manipulation state
const editingSessionId = ref<string | null>(null)
const editingName = ref('')
const renameInput = ref<HTMLInputElement[] | null>(null)
const api = useApi()

const isActive = (href: string) => {
  const pathname = route.path
  return href === '/' ? pathname === '/' : pathname.startsWith(href)
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

const handleNewChatClick = (e: MouseEvent) => {
  emit('closeMobile')
}

const handleRecentChatClick = (e: MouseEvent, sessionId: string) => {
  emit('closeMobile')
  // Simply navigate to the session page - no drawer needed
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

const getSessionMenuItems = (session: { id: string; name: string }): DropdownMenuItem[][] => {
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
  <div>
    <!-- Mobile Backdrop -->
    <Transition name="fade">
      <div
        v-if="mobileOpen"
        class="fixed inset-0 z-40 bg-stone-900/20 md:hidden"
        @click="emit('closeMobile')"
      />
    </Transition>

    <aside
      class="fixed md:static inset-y-0 left-0 z-50 flex flex-col bg-[#F5F5F4] border-r border-stone-200 transition-all duration-300 ease-in-out"
      :class="[
        open ? 'w-[260px]' : 'w-[80px]',
        mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      ]"
    >
      <div class="flex items-center justify-between p-6">
        <NuxtLink
          to="/"
          class="flex items-center gap-3 overflow-hidden"
        >
          <div class="flex items-center justify-center w-8 h-8 text-blue-600 shrink-0">
            <Waves
              :size="28"
              :stroke-width="2"
            />
          </div>
          <div
            v-if="open"
            class="flex flex-col"
          >
            <span class="font-sans font-bold tracking-tight text-stone-900 leading-tight">
              NAGARE OS
            </span>
            <span class="text-[10px] font-medium text-stone-500 uppercase tracking-widest leading-tight">
              AI Operating System
            </span>
          </div>
        </NuxtLink>
        <button
          class="md:hidden p-1 text-stone-400 hover:text-stone-800"
          aria-label="Close menu"
          @click="emit('closeMobile')"
        >
          <X
            :size="20"
            :stroke-width="1.5"
          />
        </button>
      </div>

      <div class="flex-1 overflow-y-auto py-2 space-y-6 hide-scrollbar px-4">
        <div class="space-y-1">
          <!-- New Chat Link -->
          <NuxtLink
            to="/"
            class="flex items-center justify-between w-full px-3 py-2.5 rounded-xl transition-all duration-200"
            :class="[
              isNewChatLinkActive ? 'bg-white shadow-sm border border-stone-200 text-stone-900' : 'text-stone-600 hover:bg-stone-200/50',
              !open && 'justify-center'
            ]"
            @click="handleNewChatClick"
          >
            <div class="flex items-center">
              <SquarePen
                :size="18"
                :stroke-width="1.5"
                class="shrink-0"
              />
              <span
                v-if="open"
                class="ml-3 text-sm font-medium"
              >New Chat</span>
            </div>
            <div
              v-if="open"
              class="flex items-center gap-0.5 px-1.5 py-0.5 rounded-md bg-stone-200 text-[10px] text-stone-500 font-medium"
            >
              <Command :size="10" /> K
            </div>
          </NuxtLink>
        </div>

        <!-- Recent Chats (visible when sidebar is open and active chats exist) -->
        <div v-if="open && recentSessions.length > 0" class="space-y-1">
          <div class="px-3 mb-2 flex items-center justify-between gap-2 text-[11px] font-semibold tracking-wider text-stone-400 dark:text-stone-500 uppercase">
            <span>Conversations</span>
            <button
              v-if="sessions.length > recentSessions.length"
              class="normal-case tracking-normal text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
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
                class="flex items-center w-full px-3 py-2 rounded-xl transition-all duration-200 text-stone-500 dark:text-stone-400 hover:bg-stone-200/50 dark:hover:bg-stone-800/30 hover:text-stone-800 dark:hover:text-stone-200"
                :class="[
                  isRecentChatActive(s.id)
                    ? 'bg-white dark:bg-stone-800 shadow-sm border border-stone-200/60 dark:border-stone-700 text-stone-900 dark:text-stone-100'
                    : ''
                ]"
              >
                <NuxtLink
                  :to="`/session/${s.id}`"
                  class="flex items-center flex-1 min-w-0"
                  @click="(e) => handleRecentChatClick(e, s.id)"
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
                    size="xs"
                    class="p-1"
                    aria-label="Session actions"
                    @click.stop
                  >
                    <MoreVertical :size="14" :stroke-width="1.5" class="text-stone-400" />
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
                />
              </div>
            </div>
          </div>
        </div>

        <div
          v-for="group in navGroups"
          :key="group.title"
        >
          <div
            v-if="open"
            class="px-3 mb-2 text-[11px] font-semibold tracking-wider text-stone-400 uppercase"
          >
            {{ group.title }}
          </div>
          <div class="space-y-0.5">
            <NuxtLink
              v-for="item in group.items"
              :key="item.href"
              :to="item.href"
              class="flex items-center w-full px-3 py-2.5 rounded-xl transition-all duration-200"
              :class="[
                isActive(item.href) ? 'bg-white shadow-sm border border-stone-200 text-stone-900' : 'text-stone-500 hover:bg-stone-200/50 hover:text-stone-800',
                !open && 'justify-center'
              ]"
              @click="emit('closeMobile')"
            >
              <component
                :is="item.icon"
                :size="18"
                :stroke-width="1.5"
                class="shrink-0"
              />
              <span
                v-if="open"
                class="ml-3 text-sm font-medium truncate"
              >{{ item.label }}</span>
            </NuxtLink>
          </div>
        </div>
      </div>

      <div class="p-4">
        <div
          class="p-4 rounded-2xl bg-white border border-stone-200 shadow-sm"
          :class="[!open && 'flex justify-center items-center py-4 px-2']"
        >
          <template v-if="open">
            <div class="flex items-center justify-between mb-4">
              <span class="text-xs font-semibold text-stone-900">System Status</span>
              <div class="flex items-center gap-1.5 text-[10px] font-medium text-emerald-600">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Healthy
              </div>
            </div>
            <div class="space-y-3 mb-4">
              <div class="flex items-center justify-between">
                <div class="flex flex-col">
                  <span class="text-[10px] text-stone-500">Total Queries</span>
                  <span class="text-sm font-semibold text-stone-900">24.8K</span>
                </div>
                <span class="text-[10px] font-medium text-emerald-600">+12.5%</span>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex flex-col">
                  <span class="text-[10px] text-stone-500">Avg. Latency</span>
                  <span class="text-sm font-semibold text-stone-900">320ms</span>
                </div>
                <span class="text-[10px] font-medium text-emerald-600">-8.4%</span>
              </div>
            </div>
            <NuxtLink
              to="/monitoring"
              class="w-full py-2 flex items-center justify-between text-xs font-medium text-stone-600 bg-stone-50 hover:bg-stone-100 border border-stone-200 rounded-lg px-3 transition-colors"
              @click="emit('closeMobile')"
            >
              View System Health
              <ArrowRight :size="14" />
            </NuxtLink>
          </template>
          <template v-else>
            <div class="w-2 h-2 rounded-full bg-emerald-500" />
          </template>
        </div>
      </div>
    </aside>
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
