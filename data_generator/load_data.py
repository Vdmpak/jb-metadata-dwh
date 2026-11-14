import json
from pathlib import Path

from trino.dbapi import connect

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "output"

conn = connect(
    host="localhost",
    port=8080,
    user="data_loader",
    catalog="iceberg",
    schema="jetbrains_meta",
)

cursor = conn.cursor()


def load_jsonl(filename):
    with (DATA_DIR / filename).open() as file:
        return [json.loads(line) for line in file if line.strip()]


def merge_records(table, key, columns, records, expressions=None):
    if not records:
        print(f"No records to load into {table}")
        return

    expressions = expressions or ["?"] * len(columns)

    column_names = ", ".join(columns)
    placeholders = ", ".join(expressions)

    updates = ", ".join(
        f"{column} = source.{column}"
        for column in columns
        if column != key
    )

    matched_clause = (
        f"WHEN MATCHED THEN UPDATE SET {updates}"
        if updates
        else ""
    )

    insert_columns = ", ".join(columns)
    insert_values = ", ".join(
        f"source.{column}" for column in columns
    )

    sql = f"""
        MERGE INTO iceberg.jetbrains_meta.{table} AS target
        USING (
            SELECT *
            FROM (
                VALUES ({placeholders})
            ) AS input({column_names})
        ) AS source
        ON target.{key} = source.{key}
        {matched_clause}
        WHEN NOT MATCHED THEN
            INSERT ({insert_columns})
            VALUES ({insert_values})
    """

    for record in records:
        values = [record[column] for column in columns]
        cursor.execute(sql, values)

    print(f"Merged {len(records)} records into {table}")


query_events = load_jsonl("query_events.json")
users = load_jsonl("users.json")
tables = load_jsonl("tables.json")

merge_records(
    "raw_query_events",
    "query_id",
    [
        "query_id", "user_name", "query_text",
        "started_at", "ended_at", "query_state",
        "cpu_time_ms", "processed_bytes", "physical_input_bytes",
        "peak_memory_bytes", "queued_time_ms", "accessed_tables",
    ],
    query_events,
    [
        "CAST(? AS VARCHAR)",
        "CAST(? AS VARCHAR)",
        "CAST(? AS VARCHAR)",
        "from_iso8601_timestamp(?)",
        "from_iso8601_timestamp(?)",
        "CAST(? AS VARCHAR)",
        "CAST(? AS BIGINT)",
        "CAST(? AS BIGINT)",
        "CAST(? AS BIGINT)",
        "CAST(? AS BIGINT)",
        "CAST(? AS BIGINT)",
        "CAST(? AS ARRAY(VARCHAR))",
    ],
)

merge_records(
    "raw_users",
    "user_name",
    ["user_name", "team_name"],
    users,
)

merge_records(
    "raw_tables",
    "table_name",
    ["table_name"],
    tables,
)

cursor.close()
conn.close()

print("Data loading complete.")
