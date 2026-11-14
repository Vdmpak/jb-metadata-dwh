SELECT
    table_name
FROM {{ ref('stg_tables') }}
