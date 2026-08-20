<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { onMounted, ref, watch } from 'vue'

import { ApiService } from '@/service/ApiService'
import type { LogEventOut } from '@/types/api'

const LEVEL_SEVERITY: Record<string, string> = {
  INFO: 'info',
  WARNING: 'warn',
  ERROR: 'danger',
  CRITICAL: 'danger',
  UNKNOWN: 'secondary',
}

const levelOptions = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
const serviceOptions = ref<string[]>([])
const selectedLevel = ref<string | null>(null)
const selectedService = ref<string | null>(null)
const events = ref<LogEventOut[]>([])
const loading = ref(true)

async function loadEvents() {
  loading.value = true
  events.value = await ApiService.getRecentLogs({
    level: selectedLevel.value ?? undefined,
    service: selectedService.value ?? undefined,
    limit: 300,
  })
  loading.value = false
}

onMounted(async () => {
  serviceOptions.value = await ApiService.getMetaServices()
  await loadEvents()
})

watch([selectedLevel, selectedService], loadEvents)
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h3>Recent log events</h3>
      <div class="filters">
        <Select v-model="selectedLevel" :options="levelOptions" placeholder="All levels" showClear style="width: 10rem" />
        <Select v-model="selectedService" :options="serviceOptions" placeholder="All services" showClear style="width: 12rem" />
      </div>
    </div>
    <DataTable :value="events" :loading="loading" :rows="20" paginator responsiveLayout="scroll">
      <Column header="Time">
        <template #body="{ data }">{{ new Date(data.event_ts).toLocaleString() }}</template>
      </Column>
      <Column field="service" header="Service" sortable />
      <Column header="Level">
        <template #body="{ data }">
          <Tag :severity="LEVEL_SEVERITY[data.level] ?? 'secondary'" :value="data.level" />
        </template>
      </Column>
      <Column field="message" header="Message" />
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
