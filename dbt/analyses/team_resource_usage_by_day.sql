SELECT
    team_name,
    query_date,
    query_count,
    total_cpu_time_ms,
    total_execution_time_ms,
    total_processed_bytes,
    total_physical_input_bytes,
    max_query_peak_memory_bytes,
    total_queued_time_ms
FROM iceberg.jetbrains_meta.fct_team_resource_usage_daily
WHERE query_date BETWEEN DATE '2026-11-07' AND DATE '2026-11-13'
ORDER BY query_date DESC, total_cpu_time_ms DESC;
