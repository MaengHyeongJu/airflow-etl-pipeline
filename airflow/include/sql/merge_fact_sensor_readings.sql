-- Partition-overwrite merge: safe to rerun/backfill.
DELETE FROM mart.fact_sensor_readings WHERE date_key = {{ ds_nodash }};

INSERT INTO mart.fact_sensor_readings (reading_id, device_key, date_key, metric_type, value, unit, reading_ts, is_anomaly)
SELECT
    s.reading_id,
    d.device_key,
    {{ ds_nodash }}::int AS date_key,
    s.metric_type,
    s.value,
    s.unit,
    s.reading_ts,
    s.is_anomaly
FROM staging.sensor_readings_raw s
JOIN mart.dim_device d ON d.device_id = s.device_id
WHERE s.dt = '{{ ds }}';
