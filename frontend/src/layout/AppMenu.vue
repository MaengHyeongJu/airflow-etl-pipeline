<script setup lang="ts">
import type { MenuItem } from './AppMenuItem.vue'
import AppMenuItem from './AppMenuItem.vue'

const model: MenuItem[] = [
  {
    label: 'Overview',
    items: [{ label: 'Dashboard', icon: 'pi pi-fw pi-chart-line', to: '/' }],
  },
  {
    label: 'Data',
    items: [
      { label: 'Devices', icon: 'pi pi-fw pi-microchip', to: '/devices' },
      { label: 'Sensor Readings', icon: 'pi pi-fw pi-database', to: '/sensor-readings' },
      { label: 'Logs', icon: 'pi pi-fw pi-list', to: '/logs' },
    ],
  },
]
</script>

<template>
  <ul class="menu-root">
    <AppMenuItem v-for="item in model" :key="item.label" :item="item" />
  </ul>
</template>

<style scoped>
.menu-root {
  list-style: none;
  margin: 0;
  padding: 0.5rem 0;
}
</style>
