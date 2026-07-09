<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const { user, isLoggedIn, logout } = useAuth()

const items = computed<DropdownMenuItem[][]>(() => {
  if (!isLoggedIn.value || !user.value) {
    return [
      [
        {
          label: 'Login',
          icon: 'i-lucide-log-in',
          to: '/login'
        },
        {
          label: 'Register',
          icon: 'i-lucide-user-plus',
          to: '/register'
        }
      ]
    ]
  }

  return [
    [
      {
        label: user.value.username,
        avatar: {
          src: `https://ui-avatars.com/api/?name=${encodeURIComponent(user.value.username)}&background=3b82f6&color=fff`,
          loading: 'lazy'
        },
        type: 'label'
      }
    ],
    [
      {
        label: 'Profile',
        icon: 'i-lucide-user',
        to: '/profile'
      },
      {
        label: 'Settings',
        icon: 'i-lucide-cog',
        to: '/settings'
      }
    ],
    [
      {
        label: 'Logout',
        icon: 'i-lucide-log-out',
        color: 'error',
        onSelect: () => logout()
      }
    ]
  ]
})

const userInitial = computed(() => {
  if (!user.value?.username) return 'U'
  return user.value.username.charAt(0).toUpperCase()
})
</script>

<template>
  <UDropdownMenu :items="items" :ui="{ content: 'w-48' }">
    <UButton
      color="neutral"
      variant="ghost"
      :aria-label="isLoggedIn ? `User menu: ${user?.username}` : 'User menu'"
      class="p-1"
    >
      <div
        v-if="isLoggedIn && user"
        class="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-medium text-sm shadow-sm"
      >
        {{ userInitial }}
      </div>
      <div
        v-else
        class="flex items-center justify-center w-8 h-8 rounded-full bg-stone-200 dark:bg-stone-700 text-stone-600 dark:text-stone-300 font-medium text-sm shadow-sm"
      >
        <UIcon name="i-lucide-user" :size="16" />
      </div>
    </UButton>
  </UDropdownMenu>
</template>