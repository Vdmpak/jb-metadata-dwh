import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

users = [
    {"user_name": "alice", "team_name": "platform"},
    {"user_name": "bob", "team_name": "platform"},
    {"user_name": "charlie", "team_name": "analytics"},
    {"user_name": "diana", "team_name": "analytics"},
    {"user_name": "eve", "team_name": "analytics"},
]

tables = [
    {"table_name": name}
    for name in [
        "lakehouse.sales",
        "lakehouse.customers",
        "lakehouse.orders",
        "lakehouse.products",
        "lakehouse.events",
    ]
]

query_templates = [
    ("SELECT * FROM lakehouse.sales", ["lakehouse.sales"]),
    (
        "SELECT * FROM lakehouse.orders JOIN lakehouse.customers ON orders.customer_id = customers.id",
        ["lakehouse.orders", "lakehouse.customers"],
    ),
    ("SELECT COUNT(*) FROM lakehouse.events", ["lakehouse.events"]),
    (
        "SELECT * FROM lakehouse.products WHERE price > 100",
        ["lakehouse.products"],
    ),
    (
        "SELECT * FROM lakehouse.sales JOIN lakehouse.orders ON sales.order_id = orders.id",
        ["lakehouse.sales", "lakehouse.orders"],
    ),
]

events = []
now = datetime.now(timezone.utc)

for day in range(7):
    for _ in range(15):
        user = random.choice(users)
        query_text, accessed_tables = random.choice(query_templates)

        started_at = now - timedelta(
            days=day,
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        execution_time_ms = random.randint(100, 30000)
        processed_bytes = random.randint(100_000, 500_000_000)

        events.append({
            "query_id": str(uuid.uuid4()),
            "user_name": user["user_name"],
            "query_text": query_text,
            "started_at": started_at.isoformat(),
            "ended_at": (
                started_at + timedelta(milliseconds=execution_time_ms)
            ).isoformat(),
            "query_state": random.choices(
                ["FINISHED", "FAILED"],
                weights=[95, 5],
            )[0],
            "cpu_time_ms": random.randint(50, execution_time_ms),
            "processed_bytes": processed_bytes,
            "physical_input_bytes": int(
                processed_bytes * random.uniform(0.5, 1.0)
            ),
            "peak_memory_bytes": random.randint(
                10_000_000, 500_000_000
            ),
            "queued_time_ms": random.randint(0, 5000),
            "accessed_tables": accessed_tables,
        })

def write_jsonl(filename, records):
    with (OUTPUT_DIR / filename).open("w") as file:
        for record in records:
            file.write(json.dumps(record) + "\n")

write_jsonl("query_events.json", events)
write_jsonl("users.json", users)
write_jsonl("tables.json", tables)

print(f"Generated {len(events)} query events")
print(f"Generated {len(users)} users")
print(f"Generated {len(tables)} tables")
print(f"Files saved in {OUTPUT_DIR}")
