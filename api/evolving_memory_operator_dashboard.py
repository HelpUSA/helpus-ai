from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OperatorDashboardSummary:
    """Readonly dashboard summary for HelpUSAI evolving memory.

    This module only reads a SQLite database and returns a compact
    operational summary. It does not execute commands, call the network,
    activate rules, patch files, or expose an API.
    """

    db_path: str | Path
    project_id: str = "helpusai"
    recent_limit: int = 5

    def generate(self) -> dict[str, Any]:
        path = Path(self.db_path)
        if not path.exists():
            return self._empty_summary("database_missing")

        with closing(sqlite3.connect(path)) as conn:
            conn.row_factory = sqlite3.Row
            tables = self._table_names(conn)
            counts = self._counts(conn, tables)
            recent = self._recent(conn, tables)

        failures = self._recent_failures(recent)
        status = "attention" if failures else "ok"

        return {
            "STATUS": status,
            "summary": {
                "project_id": self.project_id,
                "database": str(path),
                "readonly": True,
                "tables": sorted(tables),
            },
            "counts": counts,
            "recent": recent,
            "failures": failures,
            "next_safe_actions": self._next_safe_actions(status, counts, failures),
        }

    def _empty_summary(self, status: str) -> dict[str, Any]:
        return {
            "STATUS": status,
            "summary": {
                "project_id": self.project_id,
                "readonly": True,
            },
            "counts": {
                "events": 0,
                "commands": 0,
                "lessons": 0,
                "rules": 0,
                "evaluations": 0,
            },
            "recent": {
                "events": [],
                "commands": [],
                "lessons": [],
                "rules": [],
                "evaluations": [],
            },
            "failures": [],
            "next_safe_actions": [
                "Run readonly inspection before any patch.",
                "Confirm database path and schema before generating reports.",
            ],
        }

    def _table_names(self, conn: sqlite3.Connection) -> set[str]:
        rows = conn.execute(
            "select name from sqlite_master where type = ?",
            ("table",),
        ).fetchall()
        return {str(row["name"]) for row in rows}

    def _counts(self, conn: sqlite3.Connection, tables: set[str]) -> dict[str, int]:
        mapping = {
            "events": ["evolving_memory_events", "memory_events"],
            "commands": ["evolving_memory_commands", "memory_commands"],
            "lessons": ["evolving_memory_lessons", "memory_lessons"],
            "rules": ["evolving_memory_rules", "memory_rules"],
            "evaluations": [
                "evolving_memory_evaluation_proposals",
                "memory_evaluation_proposals",
            ],
        }
        counts: dict[str, int] = {}
        for label, candidates in mapping.items():
            table = self._first_existing_table(tables, candidates)
            counts[label] = self._count_table(conn, table) if table else 0
        return counts

    def _recent(self, conn: sqlite3.Connection, tables: set[str]) -> dict[str, list[dict[str, Any]]]:
        mapping = {
            "events": ["evolving_memory_events", "memory_events"],
            "commands": ["evolving_memory_commands", "memory_commands"],
            "lessons": ["evolving_memory_lessons", "memory_lessons"],
            "rules": ["evolving_memory_rules", "memory_rules"],
            "evaluations": [
                "evolving_memory_evaluation_proposals",
                "memory_evaluation_proposals",
            ],
        }
        recent: dict[str, list[dict[str, Any]]] = {}
        for label, candidates in mapping.items():
            table = self._first_existing_table(tables, candidates)
            recent[label] = self._recent_rows(conn, table) if table else []
        return recent

    def _first_existing_table(self, tables: set[str], candidates: list[str]) -> str | None:
        for table in candidates:
            if table in tables:
                return table
        return None

    def _count_table(self, conn: sqlite3.Connection, table: str) -> int:
        row = conn.execute(f"select count(*) as count from {table}").fetchone()
        return int(row["count"]) if row else 0

    def _recent_rows(self, conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
        rows = conn.execute(
            f"select * from {table} order by rowid desc limit ?",
            (self.recent_limit,),
        ).fetchall()
        return [{key: row[key] for key in row.keys()} for row in rows]

    def _recent_failures(self, recent: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        for label, rows in recent.items():
            for row in rows:
                text = " ".join(str(value).lower() for value in row.values())
                if "fail" in text or "error" in text or "failed" in text:
                    item = {"source": label}
                    item.update(row)
                    failures.append(item)
        return failures[: self.recent_limit]

    def _next_safe_actions(
        self,
        status: str,
        counts: dict[str, int],
        failures: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep operator dashboard readonly.",
            "Run the dashboard smoke before documentation or commit.",
            "Run base evolving memory smokes before commit.",
        ]
        if status != "ok" or failures:
            actions.insert(0, "Review recent failures before any patch.")
        if counts.get("rules", 0):
            actions.append("Do not activate rules automatically.")
        if counts.get("evaluations", 0):
            actions.append("Review evaluation proposals manually.")
        return actions


def build_operator_dashboard_summary(
    db_path: str | Path,
    project_id: str = "helpusai",
) -> dict[str, Any]:
    return OperatorDashboardSummary(db_path=db_path, project_id=project_id).generate()
