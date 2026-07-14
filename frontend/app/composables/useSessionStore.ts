import type { Session } from '~/types'

/**
 * Session store — manages active sessions and chat drawer state.
 * Uses Nuxt's built-in useState for SSR-safe shared state.
 */
export const useSessionStore = () => {
  const sessions = useState<Session[]>('session-store:active', () => [])
  const chatDrawerOpen = useState<boolean>('session-store:drawer-open', () => false)
  const drawerSessionId = useState<string | null>('session-store:drawer-session-id', () => null)

  const recentSessions = computed(() => sessions.value.slice(0, 5))

  async function loadSessions() {
    try {
      const api = useApi()
      const res = await api.sessions.list()
      sessions.value = res.sessions
    } catch (err) {
      console.error('Failed to load sessions:', err)
    }
  }

  function openDrawer(sessionId?: string) {
    chatDrawerOpen.value = true
    drawerSessionId.value = sessionId ?? null
  }

  function closeDrawer() {
    chatDrawerOpen.value = false
    drawerSessionId.value = null
  }

  function toggleDrawer() {
    chatDrawerOpen.value = !chatDrawerOpen.value
  }

  /** Call when navigating to /chat to auto-close drawer */
  function onNavigateToChat() {
    chatDrawerOpen.value = false
  }

  return {
    sessions,
    recentSessions,
    chatDrawerOpen,
    drawerSessionId,
    loadSessions,
    openDrawer,
    closeDrawer,
    toggleDrawer,
    onNavigateToChat
  }
}
