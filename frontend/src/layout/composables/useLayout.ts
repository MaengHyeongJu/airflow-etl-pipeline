import { defineStore } from 'pinia'
import { computed } from 'vue'

export const useLayoutStore = defineStore('layout', {
  state: () => ({
    sidebarCollapsed: false,
    mobileMenuActive: false,
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    toggleMobileMenu() {
      this.mobileMenuActive = !this.mobileMenuActive
    },
    closeMobileMenu() {
      this.mobileMenuActive = false
    },
  },
})

export function useLayout() {
  const store = useLayoutStore()
  return {
    sidebarCollapsed: computed(() => store.sidebarCollapsed),
    mobileMenuActive: computed(() => store.mobileMenuActive),
    toggleSidebar: store.toggleSidebar,
    toggleMobileMenu: store.toggleMobileMenu,
    closeMobileMenu: store.closeMobileMenu,
  }
}
