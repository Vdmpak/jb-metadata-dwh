SELECT
    COALESCE(u.team_name, 'unassigned') AS team_name,
    q.query_date,

    COUNT(*) AS query_count,

    SUM(q.cpu_time_ms) AS total_cpu_time_ms,
    SUM(q.execution_time_ms) AS total_execution_time_ms,

    SUM(q.processed_bytes) AS total_processed_bytes,
    SUM(q.physical_input_bytes) AS total_physical_input_bytes,

    MAX(q.peak_memory_bytes) AS max_query_peak_memory_bytes,
    SUM(q.queued_time_ms) AS total_queued_time_ms

FROM {{ ref('queries') }} q

LEFT JOIN {{ ref('users') }} u
    ON q.user_name = u.user_name

GROUP BY
    COALESCE(u.team_name, 'unassigned'),
    q.query_date
