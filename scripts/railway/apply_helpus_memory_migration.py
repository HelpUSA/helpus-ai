from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

MIGRATION_PATH = Path("migrations/helpus_memory_v1_postgres.sql")
REQUIRED_FLAG = "HELPUS_APPLY_MEMORY_MIGRATION"
EXPECTED_FLAG_VALUE = "YES_APPLY_HELPUS_MEMORY_V1"


def mask_database_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    db = parsed.path or ""
    return f"{parsed.scheme}://***:***@{host}{port}{db}"


def get_database_url() -> str:
    for key in ("DATABASE_URL", "POSTGRES_URL", "DATABASE_PUBLIC_URL"):
        value = os.getenv(key)
        if value:
            print(f"DATABASE_URL_KEY={key}")
            print(f"DATABASE_URL_MASKED={mask_database_url(value)}")
            return value
    raise SystemExit("No DATABASE_URL/POSTGRES_URL/DATABASE_PUBLIC_URL available")


def connect(database_url: str):
    try:
        import psycopg
        return "psycopg", psycopg.connect(database_url, connect_timeout=15)
    except Exception:
        import psycopg2
        return "psycopg2", psycopg2.connect(database_url, connect_timeout=15)


def main() -> int:
    print("HELPUS_MEMORY_MIGRATION_APPLY_START")

    flag = os.getenv(REQUIRED_FLAG, "")
    if flag != EXPECTED_FLAG_VALUE:
        print("APPLY_BLOCKED")
        print(f"Set {REQUIRED_FLAG}={EXPECTED_FLAG_VALUE} to apply.")
        print("No SQL was executed.")
        return 3

    if not MIGRATION_PATH.exists():
        raise SystemExit(f"Missing migration file: {MIGRATION_PATH}")

    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    lowered = sql.lower()

    blocked_terms = ["drop table", "delete from", "truncate", "alter table", "update "]
    found = [term for term in blocked_terms if term in lowered]
    if found:
        raise SystemExit("Blocked destructive or non-additive SQL terms: " + ", ".join(found))

    database_url = get_database_url()
    driver, conn = connect(database_url)
    print("DB_DRIVER=" + driver)

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    """
                    select table_name
                    from information_schema.tables
                    where table_schema = 'public'
                      and table_name in (
                        'helpus_memory_events',
                        'helpus_memory_feedback',
                        'helpus_memory_lessons',
                        'helpus_memory_rules'
                      )
                    order by table_name
                    """
                )
                tables = [row[0] for row in cur.fetchall()]
                print("TABLES_PRESENT=" + ",".join(tables))
                if len(tables) != 4:
                    raise RuntimeError("Not all HelpUS memory tables are present after migration")
    finally:
        conn.close()

    print("HELPUS_MEMORY_MIGRATION_APPLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
