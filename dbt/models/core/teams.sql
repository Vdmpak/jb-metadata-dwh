SELECT DISTINCT
    team_name
FROM {{ ref('stg_users') }}
