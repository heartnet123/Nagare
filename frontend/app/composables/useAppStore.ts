export const useAppStore = () => {
  const sidebarOpen = useState<boolean>('app-store:sidebar-open', () => true)
  const mobileMenuOpen = useState<boolean>('app-store:mobile-menu-open', () => false)

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function closeMobileMenu() {
    mobileMenuOpen.value = false
  }

  function openMobileMenu() {
    mobileMenuOpen.value = true
  }

  return {
    sidebarOpen,
    mobileMenuOpen,
    toggleSidebar,
    closeMobileMenu,
    openMobileMenu
  }
}
