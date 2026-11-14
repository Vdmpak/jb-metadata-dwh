SELECT
    q.query_id,
    q.user_name,
    accessed_table AS table_name,
    CAST(q.started_at AS DATE) AS query_date,
    'READ' AS access_type

FROM {{ ref('stg_query_events') }} q
CROSS JOIN UNNEST(q.accessed_tables) AS t(accessed_table)
