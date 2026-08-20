<script setup lang="ts">
import { onMounted, ref } from 'vue'

import DeviceTable from '@/components/DeviceTable.vue'
import { ApiService } from '@/service/ApiService'
import type { DeviceOut } from '@/types/api'

const devices = ref<DeviceOut[]>([])
const loading = ref(true)

onMounted(async () => {
  devices.value = await ApiService.getDevices()
  loading.value = false
})
</script>

<template>
  <div class="panel">
    <div class="panel-header">
      <h3>Devices</h3>
    </div>
    <DeviceTable :devices="devices" :loading="loading" />
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
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}
</style>
