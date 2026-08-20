<script setup lang="ts">
export interface MenuItem {
  label: string
  icon?: string
  to?: string
  items?: MenuItem[]
}

defineProps<{
  item: MenuItem
}>()
</script>

<template>
  <li>
    <div v-if="item.items" class="menu-section-label">{{ item.label }}</div>
    <router-link
      v-else-if="item.to"
      :to="item.to"
      class="menu-link"
      active-class="menu-link-active"
    >
      <i v-if="item.icon" :class="item.icon" />
      <span>{{ item.label }}</span>
    </router-link>
    <ul v-if="item.items" class="menu-sublist">
      <AppMenuItem v-for="child in item.items" :key="child.label" :item="child" />
    </ul>
  </li>
</template>

<style scoped>
.menu-section-label {
  padding: 0.75rem 1rem 0.25rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.menu-sublist {
  list-style: none;
  margin: 0;
  padding: 0;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 1rem;
  margin: 0.125rem 0.5rem;
  border-radius: 8px;
  color: var(--p-text-color);
  text-decoration: none;
  font-size: 0.9rem;
  transition: background-color 0.15s;
}

.menu-link:hover {
  background: var(--p-content-hover-background);
}

.menu-link-active {
  background: var(--p-primary-100);
  color: var(--p-primary-700);
  font-weight: 600;
}

.menu-link i {
  font-size: 1rem;
  width: 1.25rem;
  text-align: center;
}
</style>
