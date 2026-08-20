<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { onMounted, ref, watch } from 'vue'

import { ApiService } from '@/service/ApiService'
import type { SensorReadingOut } from '@/types/api'

const deviceOptions = ref<string[]>([])
const selectedDevice = ref<string | null>(null)
const dateRange = ref<Date[]>([
  new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  new Date(),
])
const readings = ref<SensorReadingOut[]>([])
const loading = ref(false)

function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

async function loadReadings() {
  if (!selectedDevice.value) {
    readings.value = []
    return
  }
  loading.value = true
  const [from, to] = dateRange.value
  readings.value = await ApiService.getDeviceReadings(selectedDevice.value, {
    date_from: from ? toIsoDate(from) : undefined,
    date_to: to ? toIsoDate(to) : undefined,
    limit: 1000,
  })
  loading.value = false
}

onMounted(async () => {
  deviceOptions.value = await ApiService.getMetaDevices()
  selectedDevice.value = deviceOptions.value[0] ?? null
  await loadReadings()
})

watch(selectedDevice, loadReadings)
watch(dateRange, (val) => {
  if (val?.[0] && val?.[1]) loadReadings()
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h3>Sensor readings</h3>
      <div class="filters">
        <Select v-model="selectedDevice" :options="deviceOptions" placeholder="Select device" style="width: 12rem" />
        <DatePicker v-model="dateRange" selectionMode="range" :manualInput="false" showIcon dateFormat="yy-mm-dd" />
      </div>
    </div>
    <DataTable :value="readings" :loading="loading" :rows="20" paginator responsiveLayout="scroll">
      <Column field="reading_ts" header="Time">
        <template #body="{ data }">{{ new Date(data.reading_ts).toLocaleString() }}</template>
      </Column>
      <Column field="metric_type" header="Metric" />
      <Column field="value" header="Value" />
      <Column field="unit" header="Unit" />
      <Column header="Anomaly">
        <template #body="{ data }">
          <Tag v-if="data.is_anomaly" severity="danger" value="anomaly" />
          <span v-else>-</span>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
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
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.filters {
  display: flex;
  gap: 0.75rem;
}
</style>
