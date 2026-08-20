<script setup lang="ts">
import Chart from 'primevue/chart'
import { computed } from 'vue'

import type { SensorTimeseriesPoint } from '@/types/api'

const props = defineProps<{
  points: SensorTimeseriesPoint[]
}>()

const chartData = computed(() => {
  const labels = props.points.map((p) => p.full_date)
  return {
    labels,
    datasets: [
      {
        label: 'Average value',
        data: props.points.map((p) => p.avg_value ?? 0),
        borderColor: '#0ea5e9',
        backgroundColor: 'rgba(14, 165, 233, 0.15)',
        tension: 0.35,
        fill: true,
      },
      {
        label: 'Anomalies',
        data: props.points.map((p) => p.anomaly_count),
        borderColor: '#f43f5e',
        backgroundColor: '#f43f5e',
        yAxisID: 'y1',
        type: 'bar' as const,
      },
    ],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  scales: {
    y: { position: 'left' as const, title: { display: true, text: 'avg value' } },
    y1: {
      position: 'right' as const,
      title: { display: true, text: 'anomalies' },
      grid: { drawOnChartArea: false },
    },
  },
}
</script>

<template>
  <div class="chart-wrap">
    <Chart type="line" :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.chart-wrap {
  height: 320px;
}
</style>
