<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { computed, onMounted, ref, watch } from 'vue'

import KpiCard from '@/components/KpiCard.vue'
import LogSeverityChart from '@/components/LogSeverityChart.vue'
import SensorTimeSeriesChart from '@/components/SensorTimeSeriesChart.vue'
import { ApiService } from '@/service/ApiService'
import type { KpiSummary, LogLevelSummary, SensorReadingOut, SensorTimeseriesPoint } from '@/types/api'
import { formatValue } from '@/utils/format'

const kpis = ref<KpiSummary | null>(null)
const timeseries = ref<SensorTimeseriesPoint[]>([])
const logSummary = ref<LogLevelSummary[]>([])
const anomalies = ref<SensorReadingOut[]>([])
const loading = ref(true)

const metricOptions = ['temperature_c', 'humidity_pct', 'pressure_hpa', 'vibration_mm_s', 'power_kw']
const selectedMetric = ref<string>('temperature_c')

async function loadTimeseries() {
  timeseries.value = await ApiService.getSensorTimeseries({ metric_type: selectedMetric.value })
}

async function loadAll() {
  loading.value = true
  const [kpiSummary, series, logs, recentAnomalies] = await Promise.all([
    ApiService.getKpiSummary(),
    ApiService.getSensorTimeseries({ metric_type: selectedMetric.value }),
    ApiService.getLogsSummary(),
    ApiService.getRecentAnomalies(20),
  ])
  kpis.value = kpiSummary
  timeseries.value = series
  logSummary.value = logs
  anomalies.value = recentAnomalies
  loading.value = false
}

watch(selectedMetric, loadTimeseries)
onMounted(loadAll)

const anomalyRateDisplay = computed(() =>
  kpis.value ? `${kpis.value.anomaly_rate_pct.toFixed(2)}%` : '-',
)
</script>

<template>
  <div class="dashboard">
    <div class="kpi-grid">
      <KpiCard
        title="Readings (30d)"
        :value="kpis?.total_readings ?? '-'"
        icon="pi pi-database"
        accent="#0ea5e9"
      />
      <KpiCard
        title="Active devices"
        :value="kpis?.active_devices ?? '-'"
        icon="pi pi-microchip"
        accent="#22c55e"
      />
      <KpiCard title="Anomaly rate" :value="anomalyRateDisplay" icon="pi pi-exclamation-triangle" accent="#f59e0b" />
      <KpiCard
        title="Error/critical logs (30d)"
        :value="kpis?.error_log_count ?? '-'"
        icon="pi pi-flag"
        accent="#f43f5e"
      />
    </div>

    <div class="chart-grid">
      <div class="panel panel-wide">
        <div class="panel-header">
          <h3>Sensor readings over time</h3>
          <Select
            v-model="selectedMetric"
            :options="metricOptions"
            style="width: 12rem"
          />
        </div>
        <SensorTimeSeriesChart :points="timeseries" />
      </div>
      <div class="panel">
        <div class="panel-header">
          <h3>Log severity breakdown (30d)</h3>
        </div>
        <LogSeverityChart :summary="logSummary" />
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <h3>Recent anomalies</h3>
      </div>
      <DataTable :value="anomalies" :loading="loading" :rows="10" paginator responsiveLayout="scroll">
        <Column field="device_id" header="Device" sortable />
        <Column field="metric_type" header="Metric" />
        <Column header="Value">
          <template #body="{ data }">{{ formatValue(data.value) }}</template>
        </Column>
        <Column field="unit" header="Unit" />
        <Column header="Time">
          <template #body="{ data }">{{ new Date(data.reading_ts).toLocaleString() }}</template>
        </Column>
        <Column header="">
          <template #body>
            <Tag severity="danger" value="anomaly" />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.chart-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
}

@media (max-width: 960px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}

.panel {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 12px;
  padding: 1.25rem;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}
</style>
