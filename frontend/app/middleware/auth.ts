export default defineNuxtRouteMiddleware(async (to) => {
  const authPages: readonly string[] = ['/login', '/register']
  const isAuthPage = authPages.includes(to.path)
  const auth = useAuth()

  if (!auth.isLoggedIn.value) {
    await auth.init()
  }

  if (!auth.isLoggedIn.value && !isAuthPage) {
    return navigateTo('/login')
  }

  if (auth.isLoggedIn.value && isAuthPage) {
    return navigateTo('/')
  }
})
