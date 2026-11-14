SELECT
    query_id,
    user_name,
    query_text,
    started_at,
    ended_at,
    CAST(started_at AS DATE) AS query_date,
    query_state,

    cpu_time_ms,
    processed_bytes,
    physical_input_bytes,
    peak_memory_bytes,
    queued_time_ms,

    DATE_DIFF(
        'millisecond',
        started_at,
        ended_at
    ) AS execution_time_ms,

    accessed_tables

FROM {{ ref('stg_query_events') }}
