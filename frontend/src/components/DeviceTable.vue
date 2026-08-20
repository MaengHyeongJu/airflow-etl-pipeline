<script setup lang="ts">
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Tag from 'primevue/tag'

import type { DeviceOut } from '@/types/api'

defineProps<{
  devices: DeviceOut[]
  loading?: boolean
}>()

function formatTs(ts: string | null): string {
  return ts ? new Date(ts).toLocaleString() : '-'
}
</script>

<template>
  <DataTable
    :value="devices"
    :loading="loading"
    paginator
    :rows="10"
    dataKey="device_id"
    sortField="device_id"
    :sortOrder="1"
    responsiveLayout="scroll"
  >
    <Column field="device_id" header="Device" sortable />
    <Column field="device_type" header="Type" sortable />
    <Column field="location" header="Location" />
    <Column header="Latest reading">
      <template #body="{ data }">
        <span v-if="data.latest_value !== null">{{ data.latest_value }} {{ data.unit }}</span>
        <span v-else class="text-muted">no readings yet</span>
      </template>
    </Column>
    <Column header="Last seen">
      <template #body="{ data }">{{ formatTs(data.latest_reading_ts) }}</template>
    </Column>
    <Column header="Status">
      <template #body="{ data }">
        <Tag :severity="data.is_active ? 'success' : 'danger'" :value="data.is_active ? 'active' : 'inactive'" />
      </template>
    </Column>
  </DataTable>
</template>

<style scoped>
.text-muted {
  color: var(--p-text-muted-color);
}
</style>
