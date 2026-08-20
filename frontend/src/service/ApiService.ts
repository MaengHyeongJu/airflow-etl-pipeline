import axios from 'axios'
import type {
  DeviceOut,
  KpiSummary,
  LogEventOut,
  LogLevelSummary,
  LogTimeseriesPoint,
  SensorReadingOut,
  SensorTimeseriesPoint,
} from '@/types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

export interface DateRangeParams {
  date_from?: string
  date_to?: string
}

export const ApiService = {
  async getKpiSummary(params: DateRangeParams = {}): Promise<KpiSummary> {
    const { data } = await api.get<KpiSummary>('/api/kpis/summary', { params })
    return data
  },

  async getSensorTimeseries(
    params: DateRangeParams & { metric_type?: string; device_id?: string } = {},
  ): Promise<SensorTimeseriesPoint[]> {
    const { data } = await api.get<SensorTimeseriesPoint[]>('/api/sensors/timeseries', { params })
    return data
  },

  async getRecentAnomalies(limit = 50): Promise<SensorReadingOut[]> {
    const { data } = await api.get<SensorReadingOut[]>('/api/sensors/anomalies/recent', {
      params: { limit },
    })
    return data
  },

  async getDevices(): Promise<DeviceOut[]> {
    const { data } = await api.get<DeviceOut[]>('/api/devices')
    return data
  },

  async getDeviceReadings(
    deviceId: string,
    params: DateRangeParams & { limit?: number } = {},
  ): Promise<SensorReadingOut[]> {
    const { data } = await api.get<SensorReadingOut[]>(`/api/devices/${deviceId}/readings`, { params })
    return data
  },

  async getLogsSummary(params: DateRangeParams = {}): Promise<LogLevelSummary[]> {
    const { data } = await api.get<LogLevelSummary[]>('/api/logs/summary', { params })
    return data
  },

  async getRecentLogs(
    params: { level?: string; service?: string; limit?: number } = {},
  ): Promise<LogEventOut[]> {
    const { data } = await api.get<LogEventOut[]>('/api/logs/recent', { params })
    return data
  },

  async getLogsTimeseries(params: DateRangeParams = {}): Promise<LogTimeseriesPoint[]> {
    const { data } = await api.get<LogTimeseriesPoint[]>('/api/logs/timeseries', { params })
    return data
  },

  async getMetaDevices(): Promise<string[]> {
    const { data } = await api.get<string[]>('/api/meta/devices')
    return data
  },

  async getMetaServices(): Promise<string[]> {
    const { data } = await api.get<string[]>('/api/meta/services')
    return data
  },
}
