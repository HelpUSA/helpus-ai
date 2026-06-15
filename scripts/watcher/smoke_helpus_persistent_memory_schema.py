from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.helpus_persistent_memory_schema import MEMORY_TABLES, SCHEMA_VERSION, create_schema_sql, schema_summary

sqlite_sql = "\n".join(create_schema_sql("sqlite"))
postgres_sql = "\n".join(create_schema_sql("postgres"))
summary = schema_summary()

required_tables = {
    "helpus_memory_events",
    "helpus_memory_feedback",
    "helpus_memory_lessons",
    "helpus_memory_rules",
}

actual_tables = {table.name for table in MEMORY_TABLES}
missing = required_tables - actual_tables
if missing:
    raise SystemExit("Missing memory tables: " + ", ".join(sorted(missing)))

for name in required_tables:
    if name not in sqlite_sql:
        raise SystemExit(f"Missing sqlite SQL table marker: {name}")
    if name not in postgres_sql:
        raise SystemExit(f"Missing postgres SQL table marker: {name}")

if summary["schema_version"] != SCHEMA_VERSION:
    raise SystemExit("schema version mismatch")

if summary["safety"]["automatic_rule_promotion"] is not False:
    raise SystemExit("automatic rule promotion must remain disabled")

print("OK smoke_helpus_persistent_memory_schema")

