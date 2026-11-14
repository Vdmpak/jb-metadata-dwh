SELECT
    table_name,
    query_date,
    distinct_users,
    query_count,
    read_count
FROM iceberg.jetbrains_meta.fct_table_usage_daily
WHERE query_date BETWEEN DATE '2026-11-07' AND DATE '2026-11-13'
ORDER BY query_date DESC, distinct_users DESC;
