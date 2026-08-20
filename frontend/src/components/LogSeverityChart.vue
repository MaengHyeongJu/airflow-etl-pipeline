<script setup lang="ts">
import Chart from 'primevue/chart'
import { computed } from 'vue'

import type { LogLevelSummary } from '@/types/api'

const props = defineProps<{
  summary: LogLevelSummary[]
}>()

const LEVEL_COLORS: Record<string, string> = {
  INFO: '#0ea5e9',
  WARNING: '#f59e0b',
  ERROR: '#f43f5e',
  CRITICAL: '#7f1d1d',
  UNKNOWN: '#94a3b8',
}

const chartData = computed(() => ({
  labels: props.summary.map((s) => s.level),
  datasets: [
    {
      data: props.summary.map((s) => s.event_count),
      backgroundColor: props.summary.map((s) => LEVEL_COLORS[s.level] ?? '#94a3b8'),
      hoverOffset: 6,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const } },
}
</script>

<template>
  <div class="chart-wrap">
    <Chart type="doughnut" :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-wrap {
  height: 280px;
}
</style>
