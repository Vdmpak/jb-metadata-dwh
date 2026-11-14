SELECT
    LOWER(TRIM(table_name)) AS table_name
FROM {{ source('jetbrains_meta', 'raw_tables') }}
