SELECT
    query_id,
    user_name,
    query_date,
    query_state,

    execution_time_ms,
    cpu_time_ms,
    processed_bytes,
    physical_input_bytes,
    peak_memory_bytes,
    queued_time_ms

FROM {{ ref('queries') }}
