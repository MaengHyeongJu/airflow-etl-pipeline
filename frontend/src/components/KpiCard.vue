<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    value: string | number
    icon: string
    accent?: string
  }>(),
  { accent: 'var(--p-primary-500)' },
)
</script>

<template>
  <div class="kpi-card">
    <div class="kpi-icon" :style="{ background: accent }">
      <i :class="icon" />
    </div>
    <div class="kpi-body">
      <span class="kpi-value">{{ value }}</span>
      <span class="kpi-title">{{ title }}</span>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 12px;
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.kpi-body {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--p-text-color);
  line-height: 1.2;
}

.kpi-title {
  font-size: 0.85rem;
  color: var(--p-text-muted-color);
}
</style>
