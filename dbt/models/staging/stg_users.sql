SELECT
    LOWER(TRIM(user_name)) AS user_name,
    LOWER(TRIM(team_name)) AS team_name
FROM {{ source('jetbrains_meta', 'raw_users') }}
