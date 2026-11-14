SELECT
    user_name,
    team_name
FROM {{ ref('users') }}
