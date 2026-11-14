SELECT
    table_name,
    query_date,

    COUNT(DISTINCT query_id) AS query_count,
    COUNT(DISTINCT user_name) AS distinct_users,

    COUNT_IF(access_type = 'READ') AS read_count

FROM {{ ref('query_table_accesses') }}

GROUP BY
    table_name,
    query_date
