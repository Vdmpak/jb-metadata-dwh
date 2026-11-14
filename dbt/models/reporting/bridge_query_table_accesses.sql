SELECT
    query_id,
    table_name,
    query_date,
    access_type
FROM {{ ref('query_table_accesses') }}
