INSERT INTO mart.dim_date (date_key, full_date, year, month, day, day_of_week, day_name, week_of_year, is_weekend)
SELECT
    {{ ds_nodash }}::int              AS date_key,
    d::date                            AS full_date,
    EXTRACT(YEAR FROM d)::int          AS year,
    EXTRACT(MONTH FROM d)::int         AS month,
    EXTRACT(DAY FROM d)::int           AS day,
    EXTRACT(ISODOW FROM d)::int        AS day_of_week,
    TRIM(TO_CHAR(d, 'Day'))            AS day_name,
    EXTRACT(WEEK FROM d)::int          AS week_of_year,
    EXTRACT(ISODOW FROM d) IN (6, 7)   AS is_weekend
FROM (SELECT '{{ ds }}'::date AS d) t
ON CONFLICT (date_key) DO NOTHING;
