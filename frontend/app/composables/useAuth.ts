import { computed } from 'vue'
import { useApiBase } from './useApi/utils'

type AuthUser = {
  readonly id: string
  readonly username: string
  readonly created_at: string
}

type AuthTokenResponse = {
  readonly access_token: string
}

function isStatusError(error: unknown, status: number): boolean {
  if (typeof error !== 'object' || error === null) return false

  if ('status' in error && error.status === status) return true
  if (!('response' in error) || typeof error.response !== 'object' || error.response === null) return false

  return 'status' in error.response && error.response.status === status
}

export function useAuth() {
  const user = useState<AuthUser | null>('auth:user', () => null)
  const initialized = useState('auth:initialized', () => false)
  const apiBase = useApiBase()
  const csrfToken = useCookie<string | null>('csrf_token')

  const isLoggedIn = computed(() => user.value !== null)

  const csrfHeaders = computed(() => (
    csrfToken.value ? { 'X-CSRF-Token': csrfToken.value } : undefined
  ))

  async function fetchUser(): Promise<AuthUser | null> {
    try {
      const currentUser = await $fetch<AuthUser>('/api/auth/me', {
        baseURL: apiBase,
        credentials: 'include',
        headers: import.meta.server ? useRequestHeaders(['cookie']) : undefined
      })
      user.value = currentUser
      return currentUser
    } catch (error) {
      if (isStatusError(error, 401)) {
        user.value = null
        return null
      }
      throw error
    }
  }

  async function login(username: string, password: string): Promise<AuthUser | null> {
    await $fetch<AuthTokenResponse>('/api/auth/login', {
      baseURL: apiBase,
      method: 'POST',
      body: { username, password },
      credentials: 'include',
      headers: csrfHeaders.value
    })

    return await fetchUser()
  }

  async function register(username: string, password: string): Promise<AuthUser | null> {
    await $fetch<AuthTokenResponse>('/api/auth/register', {
      baseURL: apiBase,
      method: 'POST',
      body: { username, password },
      credentials: 'include',
      headers: csrfHeaders.value
    })

    return await fetchUser()
  }

  async function logout(): Promise<void> {
    await $fetch('/api/auth/logout', {
      baseURL: apiBase,
      method: 'POST',
      credentials: 'include',
      headers: csrfHeaders.value
    })
    user.value = null
    await navigateTo('/login')
  }

  async function init(): Promise<AuthUser | null> {
    if (initialized.value) return user.value

    initialized.value = true
    return await fetchUser()
  }

  return {
    user,
    isLoggedIn,
    login,
    register,
    logout,
    fetchUser,
    init
  }
}
