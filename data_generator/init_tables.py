
from trino.dbapi import connect


def main():
    conn = connect(
        host="localhost",
        port=8080,
        user="data_loader",
        catalog="iceberg",
        schema="jetbrains_meta",
    )

    statements = [
        """
        CREATE SCHEMA IF NOT EXISTS iceberg.jetbrains_meta
        """,
        """
        CREATE TABLE IF NOT EXISTS iceberg.jetbrains_meta.raw_query_events (
            query_id VARCHAR,
            user_name VARCHAR,
            query_text VARCHAR,
            started_at TIMESTAMP(3) WITH TIME ZONE,
            ended_at TIMESTAMP(3) WITH TIME ZONE,
            query_state VARCHAR,
            cpu_time_ms BIGINT,
            processed_bytes BIGINT,
            physical_input_bytes BIGINT,
            peak_memory_bytes BIGINT,
            queued_time_ms BIGINT,
            accessed_tables ARRAY(VARCHAR)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS iceberg.jetbrains_meta.raw_users (
            user_name VARCHAR,
            team_name VARCHAR
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS iceberg.jetbrains_meta.raw_tables (
            table_name VARCHAR
        )
        """,
    ]

    try:
        cursor = conn.cursor()

        for statement in statements:
            cursor.execute(statement)
            print("Executed:", " ".join(statement.split())[:100])

        print("\nIceberg schema and raw tables initialized successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
