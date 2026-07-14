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

function getErrorStatus(error: unknown): number | null {
  if (typeof error !== 'object' || error === null) return null

  const value = error as {
    status?: unknown
    statusCode?: unknown
    response?: { status?: unknown } | null
  }
  const status = value.status ?? value.statusCode ?? value.response?.status
  return typeof status === 'number' ? status : null
}

function isStatusError(error: unknown, status: number): boolean {
  return getErrorStatus(error) === status
}

export function getAuthErrorMessage(error: unknown, action: 'login' | 'register'): string {
  switch (getErrorStatus(error)) {
    case 400:
      return 'Request is invalid. Check your details and try again.'
    case 401:
      return action === 'login'
        ? 'Invalid username or password.'
        : 'Authentication failed. Try again.'
    case 403:
      return 'Request blocked. Refresh page and try again.'
    case 404:
      return 'Authentication service is unavailable. Try again later.'
    case 409:
      return action === 'register' ? 'Username already taken.' : 'Account already exists.'
    case 422:
      return 'Enter valid username and password.'
    case 408:
    case 429:
      return 'Too many requests. Wait a moment and try again.'
    default: {
      const status = getErrorStatus(error)
      return status !== null && status >= 500
        ? 'Server error. Try again later.'
        : 'Unable to reach server. Check your connection and try again.'
    }
  }
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
