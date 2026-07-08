<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Home,
  SquarePen,
  Waves,
  X,
  ArrowRight,
  Command,
  MessageSquare,
  BarChart2,
  Database,
  Target,
  FileText,
  Workflow,
  Bot,
  Activity,
  Box,
  BookOpen,
  Settings,
  Cpu
} from '@lucide/vue'

const navGroups = [
  {
    title: 'EVALUATIONS',
    items: [
      { href: '/evaluations', icon: BarChart2, label: 'Evaluations' },
      { href: '/datasets', icon: Database, label: 'Datasets' },
      { href: '/benchmark', icon: Target, label: 'Benchmark' },
      { href: '/logs', icon: FileText, label: 'Logs' }
    ]
  },
  {
    title: 'SYSTEM OS',
    items: [
      { href: '/pipeline', icon: Workflow, label: 'Pipeline' },
      { href: '/agents', icon: Bot, label: 'Agents' },
      { href: '/monitoring', icon: Activity, label: 'Monitoring' },
      { href: '/analytics', icon: BarChart2, label: 'Analytics' }
    ]
  },
  {
    title: 'CONFIGURATION',
    items: [
      { href: '/models', icon: Box, label: 'Models' },
      { href: '/knowledge', icon: BookOpen, label: 'Knowledge' },
      { href: '/mcp', icon: Cpu, label: 'MCP Servers' },
      { href: '/settings', icon: Settings, label: 'Settings' }
    ]
  }
]

defineProps<{
  open: boolean
  mobileOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'closeMobile'): void
}>()

const route = useRoute()
const api = useApi()
const sessionsList = useState<any[]>('active-sessions', () => [])

const recentSessions = computed(() => sessionsList.value.slice(0, 5))

onMounted(async () => {
  if (sessionsList.value.length === 0) {
    try {
      const res = await api.sessions.list()
      sessionsList.value = res.sessions
    } catch (error) {
      console.error('Sidebar failed to load sessions:', error)
    }
  }
})

const isActive = (href: string) => {
  const pathname = route.path
  return href === '/' ? pathname === '/' : pathname.startsWith(href)
}

// Drawer state
const isChatDrawerOpen = useState<boolean>('chat-drawer-open', () => false)
const drawerSessionId = useState<string | null>('chat-drawer-session-id', () => null)

const isNewChatLinkActive = computed(() => {
  if (route.path === '/chat') {
    return !route.query.session
  }
  return isChatDrawerOpen.value && !drawerSessionId.value
})

const isRecentChatActive = (sessionId: string) => {
  if (route.path === '/chat') {
    return route.query.session === sessionId
  }
  return isChatDrawerOpen.value && drawerSessionId.value === sessionId
}

const handleNewChatClick = (e: MouseEvent) => {
  emit('closeMobile')
  if (route.path !== '/chat') {
    e.preventDefault()
    isChatDrawerOpen.value = true
    drawerSessionId.value = null
  }
}

const handleRecentChatClick = (e: MouseEvent, sessionId: string) => {
  emit('closeMobile')
  if (route.path !== '/chat') {
    e.preventDefault()
    isChatDrawerOpen.value = true
    drawerSessionId.value = sessionId
  }
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
          <!-- Home Link -->
          <NuxtLink
            to="/"
            class="flex items-center w-full px-3 py-2.5 rounded-xl transition-all duration-200"
            :class="[
              isActive('/') ? 'bg-white shadow-sm border border-stone-200 text-stone-900' : 'text-stone-500 hover:bg-stone-200/50 hover:text-stone-800',
              !open && 'justify-center'
            ]"
            @click="emit('closeMobile')"
          >
            <Home
              :size="18"
              :stroke-width="1.5"
              class="shrink-0"
            />
            <span
              v-if="open"
              class="ml-3 text-sm font-medium truncate"
            >Home</span>
          </NuxtLink>

          <!-- Chat Link -->
          <NuxtLink
            to="/chat"
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
          <div class="px-3 mb-2 text-[11px] font-semibold tracking-wider text-stone-400 dark:text-stone-500 uppercase">
            Recent Chats
          </div>
          <div class="space-y-0.5">
            <NuxtLink
              v-for="s in recentSessions"
              :key="s.id"
              :to="`/chat?session=${s.id}`"
              class="flex items-center w-full px-3 py-2 rounded-xl transition-all duration-200 group text-stone-500 dark:text-stone-400 hover:bg-stone-200/50 dark:hover:bg-stone-800/30 hover:text-stone-800 dark:hover:text-stone-200"
              :class="[
                isRecentChatActive(s.id)
                  ? 'bg-white dark:bg-stone-800 shadow-sm border border-stone-200/60 dark:border-stone-700 text-stone-900 dark:text-stone-100'
                  : ''
              ]"
              @click="(e) => handleRecentChatClick(e, s.id)"
            >
              <MessageSquare
                :size="15"
                :stroke-width="1.5"
                class="shrink-0 text-stone-400 mr-2"
              />
              <span class="text-xs font-medium truncate flex-1 leading-none">{{ s.name }}</span>
            </NuxtLink>
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
