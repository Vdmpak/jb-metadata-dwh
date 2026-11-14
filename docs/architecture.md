# Metadata Data Warehouse Architecture

## 1. Purpose

The purpose of this warehouse is to collect and analyse Trino query execution metadata.

It answers two main questions:

1. How many distinct users access each warehouse table over a selected period?
2. How much query and compute resource does each team consume over a selected period?

The implementation is a local demonstration using synthetic query events. MinIO provides S3-compatible object storage, Apache Iceberg manages analytical tables, Trino provides SQL access, and dbt performs transformations.

## 2. High-level architecture

```text
                  Synthetic query events
                           |
                           v
                   Python generator
                           |
                           v
                    Local JSONL files
                           |
                           v
                    Python data loader
                           |
                           v
                     Trino engine
                           |
                           v
                  Apache Iceberg tables
                           |
                           v
                   MinIO object storage
                     (S3-compatible)

               Apache Iceberg REST catalog
                  manages table metadata

                           |
                           v
                    dbt transformations
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Staging         Core        Reporting
                                       |
                            +----------+----------+
                            |                     |
                            v                     v
                     Table usage fact     Team resource fact
```

### Components

| Component            | Responsibility                                                |
| -------------------- | ------------------------------------------------------------- |
| Python generator     | Creates synthetic query events, users and table metadata      |
| JSONL files          | Provide local input data for ingestion                        |
| Python loader        | Loads and merges records into Iceberg tables                  |
| MinIO                | Stores Iceberg data files using an S3-compatible API          |
| Iceberg REST catalog | Maintains Iceberg table metadata                              |
| Trino                | Queries Iceberg tables and executes SQL transformations       |
| dbt-trino            | Builds staging, core and reporting models and runs data tests |

## 3. Source data

The demonstration uses three input datasets.

### Query events

Grain: one row per query execution.

Important attributes:

- `query_id`: unique query execution identifier.
- `user_name`: submitting user.
- `query_text`: submitted SQL statement.
- `started_at`, `ended_at`: query timestamps.
- `query_state`: execution status.
- `cpu_time_ms`: CPU time consumed.
- `processed_bytes`: bytes processed.
- `physical_input_bytes`: physical input bytes read.
- `peak_memory_bytes`: query peak memory.
- `queued_time_ms`: time spent waiting in the queue.
- `accessed_tables`: array of tables accessed by the query.

### Users

Grain: one row per user.

Attributes:

- `user_name`: user identifier.
- `team_name`: associated team.

### Tables

Grain: one row per warehouse table.

Attribute:

- `table_name`: fully qualified table name.

The generated dataset contains 105 query events, 5 users, 2 teams and 5 warehouse tables.

## 4. Transformation layers

The dbt project uses three logical layers.

### Staging

Staging models standardise the source data with light cleaning and type handling.

- `stg_query_events`
- `stg_users`
- `stg_tables`

These models reference the raw Iceberg source tables.

### Core

Core models represent reusable entities and relationships.

| Model                  | Grain                        | Description                                       |
| ---------------------- | ---------------------------- | ------------------------------------------------- |
| `queries`              | One row per query            | Query attributes, timestamps and resource metrics |
| `users`                | One row per user             | User-to-team mapping                              |
| `teams`                | One row per team             | Unique team reference                             |
| `tables`               | One row per table            | Unique warehouse table reference                  |
| `query_table_accesses` | One row per query/table pair | Tables accessed by each query                     |

The `query_table_accesses` model unnests the source array of accessed tables.

A query that accesses three tables therefore produces three records in this model.

### Reporting

Reporting models are designed for analytical consumption.

| Model                           | Grain                        | Description                     |
| ------------------------------- | ---------------------------- | ------------------------------- |
| `dim_user`                      | One row per user             | User dimension                  |
| `dim_team`                      | One row per team             | Team dimension                  |
| `dim_table`                     | One row per table            | Table dimension                 |
| `fct_queries`                   | One row per query            | Query-level metrics             |
| `bridge_query_table_accesses`   | One row per query/table pair | Query-to-table relationship     |
| `fct_table_usage_daily`         | One row per table per day    | Daily table usage               |
| `fct_team_resource_usage_daily` | One row per team per day     | Daily team resource consumption |

## 5. Entity relationships

The principal relationships are:

```text
                 teams
                   |
                   | one team has many users
                   |
                 users
                   |
                   | one user submits many queries
                   |
                 queries
                   |
                   | one query can access many tables
                   |
          query_table_accesses
                   |
                   | many queries can access one table
                   |
                 tables
```

The query-to-table relationship is many-to-many.

It is represented by `query_table_accesses`, which acts as a bridge between queries and tables.

The reporting layer preserves this relationship through `bridge_query_table_accesses`.

An important aggregation rule is that query-level resource metrics must not be aggregated after joining to the query/table bridge. Doing so would multiply resource values for queries accessing multiple tables.

Table usage and team resource consumption are therefore calculated independently.

## 6. Analytical metrics

### Table usage

The `fct_table_usage_daily` model aggregates query/table access records by table and date.

Metrics:

- `query_count`: number of distinct queries accessing the table.
- `distinct_users`: number of distinct users accessing the table.
- `read_count`: number of recorded read accesses.

The current synthetic source does not distinguish read and write operations. Accesses are therefore labelled `READ` as a documented demonstration assumption.

In production, access types should come from actual query execution or audit metadata.

### Team resource consumption

The `fct_team_resource_usage_daily` model joins query events to user/team metadata and aggregates by team and date.

Metrics:

- `query_count`: number of query executions.
- `total_cpu_time_ms`: total CPU time.
- `total_execution_time_ms`: total elapsed execution time.
- `total_processed_bytes`: total processed bytes.
- `total_physical_input_bytes`: total physical input bytes.
- `max_query_peak_memory_bytes`: maximum individual query peak memory within the team/day group.
- `total_queued_time_ms`: total queued time.

CPU time and execution time measure different aspects of query resource consumption and should not be treated as interchangeable.

The maximum query peak memory is not a measurement of total concurrent team memory usage.

Queries with missing user/team mappings are retained using a left join and assigned to the `unassigned` team. This prevents incomplete mapping metadata from silently excluding resource consumption.

## 7. Ingestion and update strategy

The Python loader uses Iceberg `MERGE` statements to make repeated ingestion idempotent.

Matching keys:

| Dataset      | Matching key |
| ------------ | ------------ |
| Query events | `query_id`   |
| Users        | `user_name`  |
| Tables       | `table_name` |

Existing records are updated when their keys match. New records are inserted when no matching key exists.

The same input can therefore be loaded repeatedly without duplicating query events, users or tables.

The current dbt models use table materializations and full rebuilds. This is suitable for the small demonstration dataset.

### Production update strategy

For a production warehouse, I would introduce incremental processing:

1. Ingest new query events using a stable query identifier.
2. Deduplicate events and retain the latest available state for each query.
3. Account for late-arriving events and changes to query metadata.
4. Reprocess affected dates or a rolling window of recent dates.
5. Rebuild or incrementally update affected daily aggregates.
6. Periodically reconcile reporting totals against source events.

The incremental strategy should be validated against the deployed dbt-trino adapter and Iceberg catalog capabilities before relying on specific `MERGE` or partition-overwrite behaviour.

## 8. Data quality

The dbt project includes tests for:

- Unique and non-null identifiers.
- Required attributes.
- Relationships between facts, dimensions and bridge records.
- Accepted access types.

The full dbt build completed successfully with 64 passing nodes (models and tests), with no warnings or errors.

Additional production checks should include:

- Valid query timestamp ordering.
- Non-negative resource metrics.
- Valid user and team mappings.
- Monitoring for unexpected changes in event volume or schema.
- Reconciliation of source and reporting record counts.

## 9. Production considerations and limitations

The local implementation demonstrates the logical architecture and analytical transformations, but several aspects would need further work in a production deployment.

### User and team history

The demonstration uses a static user-to-team mapping.

A production implementation should use effective-dated membership records, allowing each query to be associated with the team that the user belonged to when the query started.

### Query access metadata

The demonstration uses synthetic SQL templates and an explicit list of accessed tables.

A production ingestion process should obtain table access information from reliable Trino query metadata or audit events. It should also distinguish reads, writes and other relevant operations.

Queries that access multiple catalogs or external data sources should preserve fully qualified source identifiers, such as catalog, schema and table, rather than relying only on table names.

### Security and operations

A production deployment should also include:

- Appropriate access controls and least-privilege credentials.
- Secure secret management.
- Monitoring of ingestion and transformation failures.
- Retention and lifecycle policies for query metadata.
- Data minimisation or masking where query text contains sensitive information.
- Scheduled ingestion and transformation orchestration.

These are production recommendations, not capabilities implemented in the local demonstration.

## 10. Summary

The proposed warehouse separates raw query metadata, reusable core entities and analytical reporting models.

The query/table bridge preserves multi-table access relationships, while independent fact aggregation prevents resource metrics from being duplicated.

The two reporting facts provide daily historical metrics for table usage and team resource consumption. Idempotent ingestion and dbt data tests provide a foundation for reliable updates and further production development.
