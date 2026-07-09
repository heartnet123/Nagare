<script setup lang="ts">
const { login } = useAuth()

definePageMeta({
  layout: false
})

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')

async function onSubmit() {
  loading.value = true
  errorMessage.value = ''

  try {
    await login(form.username, form.password)
    await navigateTo('/')
  } catch (error) {
    if (error instanceof Error) {
      errorMessage.value = error.message
    } else {
      errorMessage.value = 'Unable to sign in.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-[100dvh] items-center justify-center bg-stone-50 px-4 py-12 text-stone-900 dark:bg-stone-950 dark:text-stone-50">
    <div class="w-full max-w-md">
      <div class="mb-8 text-center">
        <p class="text-sm font-medium uppercase tracking-[0.28em] text-emerald-600 dark:text-emerald-400">
          Nagare OS
        </p>
        <h1 class="mt-3 text-3xl font-semibold tracking-tight">
          Welcome back
        </h1>
        <p class="mt-2 text-sm text-stone-500 dark:text-stone-400">
          Sign in to operate your agent workspace.
        </p>
      </div>

      <UCard class="border border-stone-200 bg-white/90 shadow-sm dark:border-stone-800 dark:bg-stone-900/80">
        <UForm
          :state="form"
          class="space-y-5"
          @submit="onSubmit"
        >
          <UAlert
            v-if="errorMessage"
            color="error"
            variant="soft"
            :description="errorMessage"
          />

          <UFormField
            label="Username"
            name="username"
            required
          >
            <UInput
              v-model="form.username"
              autocomplete="username"
              placeholder="agent-operator"
              class="w-full"
            />
          </UFormField>

          <UFormField
            label="Password"
            name="password"
            required
          >
            <UInput
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="Enter your password"
              class="w-full"
            />
          </UFormField>

          <UButton
            type="submit"
            color="primary"
            block
            :loading="loading"
          >
            Sign in
          </UButton>
        </UForm>
      </UCard>

      <p class="mt-6 text-center text-sm text-stone-500 dark:text-stone-400">
        Need an account?
        <NuxtLink
          to="/register"
          class="font-medium text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
        >
          Create one
        </NuxtLink>
      </p>
    </div>
  </main>
</template>
