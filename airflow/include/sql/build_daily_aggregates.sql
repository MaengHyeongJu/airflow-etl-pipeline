DELETE FROM mart.agg_daily_device_metrics WHERE date_key = {{ ds_nodash }};

INSERT INTO mart.agg_daily_device_metrics (date_key, device_key, metric_type, reading_count, avg_value, min_value, max_value, anomaly_count)
SELECT
    date_key,
    device_key,
    metric_type,
    count(*)                                       AS reading_count,
    avg(value)                                      AS avg_value,
    min(value)                                       AS min_value,
    max(value)                                       AS max_value,
    sum(CASE WHEN is_anomaly THEN 1 ELSE 0 END)      AS anomaly_count
FROM mart.fact_sensor_readings
WHERE date_key = {{ ds_nodash }}
GROUP BY date_key, device_key, metric_type;

DELETE FROM mart.agg_daily_log_summary WHERE date_key = {{ ds_nodash }};

INSERT INTO mart.agg_daily_log_summary (date_key, service, level, event_count)
SELECT
    date_key,
    service,
    level,
    count(*) AS event_count
FROM mart.fact_log_events
WHERE date_key = {{ ds_nodash }}
GROUP BY date_key, service, level;
