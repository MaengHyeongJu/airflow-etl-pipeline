import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '@/layout/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'devices', name: 'devices', component: () => import('@/views/Devices.vue') },
        {
          path: 'sensor-readings',
          name: 'sensor-readings',
          component: () => import('@/views/SensorReadings.vue'),
        },
        { path: 'logs', name: 'logs', component: () => import('@/views/Logs.vue') },
      ],
    },
  ],
})

export default router
