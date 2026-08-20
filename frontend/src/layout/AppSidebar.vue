<script setup lang="ts">
import AppMenu from './AppMenu.vue'
import { useLayout } from './composables/useLayout'

const { sidebarCollapsed, mobileMenuActive, closeMobileMenu } = useLayout()
</script>

<template>
  <div
    class="sidebar"
    :class="{ 'sidebar-collapsed': sidebarCollapsed, 'sidebar-mobile-active': mobileMenuActive }"
  >
    <div class="sidebar-brand">
      <i class="pi pi-sitemap" />
      <span v-show="!sidebarCollapsed" class="sidebar-brand-text">ETL Ops</span>
    </div>
    <div class="sidebar-menu-container" @click="closeMobileMenu">
      <AppMenu />
    </div>
  </div>
  <div v-if="mobileMenuActive" class="sidebar-mask" @click="closeMobileMenu" />
</template>

<style scoped>
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--p-content-background);
  border-right: 1px solid var(--p-content-border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  overflow: hidden;
}

.sidebar-collapsed {
  width: 74px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1.1rem 1.25rem;
  font-weight: 700;
  font-size: 1.05rem;
  border-bottom: 1px solid var(--p-content-border-color);
  color: var(--p-primary-600);
  white-space: nowrap;
}

.sidebar-brand i {
  font-size: 1.3rem;
}

.sidebar-menu-container {
  flex: 1;
  overflow-y: auto;
}

.sidebar-mask {
  display: none;
}

@media (max-width: 960px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    transform: translateX(-100%);
    width: 260px;
  }

  .sidebar-mobile-active {
    transform: translateX(0);
  }

  .sidebar-mask {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 20;
  }
}
</style>
