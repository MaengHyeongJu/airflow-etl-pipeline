<script setup lang="ts">
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import Button from 'primevue/button'
import { useRoute } from 'vue-router'

import { useLayout } from './composables/useLayout'

const route = useRoute()
const { toggleSidebar, toggleMobileMenu } = useLayout()

function onMenuToggle() {
  if (window.innerWidth <= 960) {
    toggleMobileMenu()
  } else {
    toggleSidebar()
  }
}
</script>

<template>
  <header class="topbar">
    <div class="topbar-left">
      <Button icon="pi pi-bars" text rounded aria-label="Toggle menu" @click="onMenuToggle" />
      <span class="topbar-title">{{ String(route.name ?? '') }}</span>
    </div>
    <div class="topbar-right">
      <Button icon="pi pi-bell" text rounded aria-label="Notifications">
        <template #icon>
          <span class="p-overlay-badge">
            <i class="pi pi-bell" />
            <Badge severity="danger" size="small" />
          </span>
        </template>
      </Button>
      <Avatar label="A" shape="circle" style="background-color: var(--p-primary-500); color: #fff" />
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.25rem;
  background: var(--p-content-background);
  border-bottom: 1px solid var(--p-content-border-color);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.topbar-title {
  font-weight: 600;
  text-transform: capitalize;
  color: var(--p-text-color);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
