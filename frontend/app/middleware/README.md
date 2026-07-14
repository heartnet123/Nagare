# Route Middleware

Place route guard middleware here.

Example:

```ts
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const token = useCookie('auth-token')
  if (!token.value && to.path !== '/login') {
    return navigateTo('/login')
  }
})
```

Middleware files are auto-registered by Nuxt based on filename.
Global middleware uses `.global.ts` suffix.
