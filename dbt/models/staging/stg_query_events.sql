SELECT
    query_id,
    LOWER(TRIM(user_name)) AS user_name,
    TRIM(query_text) AS query_text,
    started_at,
    ended_at,
    UPPER(TRIM(query_state)) AS query_state,

    CAST(cpu_time_ms AS BIGINT) AS cpu_time_ms,
    CAST(processed_bytes AS BIGINT) AS processed_bytes,
    CAST(physical_input_bytes AS BIGINT) AS physical_input_bytes,
    CAST(peak_memory_bytes AS BIGINT) AS peak_memory_bytes,
    CAST(queued_time_ms AS BIGINT) AS queued_time_ms,

    accessed_tables

FROM {{ source('jetbrains_meta', 'raw_query_events') }}
