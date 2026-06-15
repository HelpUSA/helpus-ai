from pathlib import Path

sql_path = Path("migrations/helpus_memory_v1_postgres.sql")
if not sql_path.exists():
    raise SystemExit("Missing migration SQL")

sql = sql_path.read_text(encoding="utf-8")
lowered = sql.lower()

required = [
    "begin;",
    "commit;",
    "create table if not exists helpus_memory_events",
    "create table if not exists helpus_memory_feedback",
    "create table if not exists helpus_memory_lessons",
    "create table if not exists helpus_memory_rules",
    "create index if not exists idx_helpus_memory_events_created_at",
    "create index if not exists idx_helpus_memory_feedback_status",
    "create index if not exists idx_helpus_memory_lessons_status",
    "create unique index if not exists ux_helpus_memory_rules_key_status",
    "jsonb",
    "timestamptz not null default now()",
]

missing = [item for item in required if item not in lowered]
if missing:
    raise SystemExit("Missing SQL markers: " + ", ".join(missing))

blocked = ["drop table", "delete from", "truncate", "alter table", "update "]
found = [item for item in blocked if item in lowered]
if found:
    raise SystemExit("Blocked SQL terms present: " + ", ".join(found))

print("OK smoke_helpus_memory_postgres_migration_sql")
