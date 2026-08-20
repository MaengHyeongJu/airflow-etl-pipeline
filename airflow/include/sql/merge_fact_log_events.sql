-- Partition-overwrite merge: safe to rerun/backfill.
DELETE FROM mart.fact_log_events WHERE date_key = {{ ds_nodash }};

INSERT INTO mart.fact_log_events (log_id, date_key, service, level, message, event_ts)
SELECT
    l.log_id,
    {{ ds_nodash }}::int AS date_key,
    l.service,
    l.level,
    l.message,
    l.event_ts
FROM staging.log_events_raw l
WHERE l.dt = '{{ ds }}';
