export interface KpiSummary {
  date_from: string
  date_to: string
  total_readings: number
  active_devices: number
  anomaly_count: number
  anomaly_rate_pct: number
  log_event_count: number
  error_log_count: number
}

export interface SensorTimeseriesPoint {
  full_date: string
  metric_type: string
  reading_count: number
  avg_value: number | null
  min_value: number | null
  max_value: number | null
  anomaly_count: number
}

export interface DeviceOut {
  device_id: string
  device_type: string
  location: string | null
  install_date: string | null
  is_active: boolean
  latest_reading_ts: string | null
  latest_value: number | null
  metric_type: string | null
  unit: string | null
}

export interface SensorReadingOut {
  reading_id: string
  device_id: string
  metric_type: string
  value: number
  unit: string | null
  reading_ts: string
  is_anomaly: boolean
}

export interface LogLevelSummary {
  level: string
  event_count: number
}

export interface LogEventOut {
  log_id: string
  service: string
  level: string
  message: string | null
  event_ts: string
}

export interface LogTimeseriesPoint {
  full_date: string
  level: string
  event_count: number
}
