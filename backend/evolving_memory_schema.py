from __future__ import annotations
import sqlite3

SCHEMA_VERSION="2026-06-14.micro1"
TABLES={
"agents": "id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, role TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', model_provider TEXT, model_name TEXT, system_prompt TEXT, capabilities_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"conversations": "id TEXT PRIMARY KEY, title TEXT NOT NULL, project_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', current_phase TEXT, summary TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"messages": "id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id), source_agent_id TEXT REFERENCES agents(id), target_agent_id TEXT REFERENCES agents(id), direction TEXT NOT NULL, kind TEXT NOT NULL, content TEXT NOT NULL, metadata_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'created', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, read_at TEXT, ack_at TEXT",
"agent_state": "id TEXT PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id), project_id TEXT NOT NULL, state_json TEXT NOT NULL DEFAULT '{}', attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count>=0), last_error TEXT, cooldown_until TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(agent_id, project_id)",
"experience_events": "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, agent_id TEXT REFERENCES agents(id), event_type TEXT NOT NULL, input_text TEXT, output_text TEXT, metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"command_requests": "id TEXT PRIMARY KEY, command_id TEXT NOT NULL UNIQUE, requested_by_agent_id TEXT REFERENCES agents(id), project_id TEXT NOT NULL, cwd TEXT NOT NULL, command_json TEXT NOT NULL, reason TEXT NOT NULL, risk_level TEXT NOT NULL CHECK(risk_level IN ('low','medium','high')), status TEXT NOT NULL DEFAULT 'proposed', requires_confirmation INTEGER NOT NULL DEFAULT 1 CHECK(requires_confirmation IN (0,1)), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, approved_at TEXT, started_at TEXT, finished_at TEXT",
"command_results": "id TEXT PRIMARY KEY, command_request_id TEXT NOT NULL REFERENCES command_requests(id), return_code INTEGER NOT NULL, stdout TEXT NOT NULL DEFAULT '', stderr TEXT NOT NULL DEFAULT '', files_changed_json TEXT NOT NULL DEFAULT '[]', diff_stat TEXT NOT NULL DEFAULT '', summary TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"memories": "id TEXT PRIMARY KEY, agent_id TEXT REFERENCES agents(id), project_id TEXT NOT NULL, scope TEXT NOT NULL, category TEXT NOT NULL, content TEXT NOT NULL, summary TEXT, importance INTEGER NOT NULL DEFAULT 50 CHECK(importance>=0 AND importance<=100), confidence REAL NOT NULL DEFAULT 0.5 CHECK(confidence>=0 AND confidence<=1), source_type TEXT NOT NULL, source_id TEXT, valid_from TEXT, valid_until TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"lessons": "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, trigger_event_id TEXT REFERENCES experience_events(id), problem TEXT NOT NULL, root_cause TEXT NOT NULL, lesson TEXT NOT NULL, rule_text TEXT, severity TEXT NOT NULL CHECK(severity IN ('low','medium','high')), status TEXT NOT NULL DEFAULT 'draft', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"rules": "id TEXT PRIMARY KEY, scope TEXT NOT NULL, name TEXT NOT NULL, rule_text TEXT NOT NULL, priority INTEGER NOT NULL DEFAULT 100, enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)), status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','deprecated','rejected')), source_lesson_id TEXT REFERENCES lessons(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(scope,name)",
"self_improvement_tasks": "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, title TEXT NOT NULL, problem TEXT NOT NULL, proposed_solution TEXT NOT NULL, target_files_json TEXT NOT NULL DEFAULT '[]', risk_level TEXT NOT NULL CHECK(risk_level IN ('low','medium','high')), status TEXT NOT NULL DEFAULT 'proposed', created_by_agent_id TEXT REFERENCES agents(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, completed_at TEXT",
"code_changes": "id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES self_improvement_tasks(id), branch TEXT NOT NULL, commit_hash TEXT, files_changed_json TEXT NOT NULL DEFAULT '[]', diff_summary TEXT NOT NULL, validation_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
"db_migrations": "id TEXT PRIMARY KEY, task_id TEXT REFERENCES self_improvement_tasks(id), migration_name TEXT NOT NULL UNIQUE, migration_sql TEXT NOT NULL, rollback_sql TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'proposed', environment TEXT NOT NULL DEFAULT 'local', applied_at TEXT, validated_at TEXT",
"evaluations": "id TEXT PRIMARY KEY, project_id TEXT NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL, target TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'proposed', command_json TEXT NOT NULL DEFAULT '[]', result_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(project_id,name)"
}
REQUIRED = {
    "agents": {"id", "name", "role", "status", "capabilities_json", "created_at", "updated_at"},
    "conversations": {"id", "title", "project_id", "status", "created_at", "updated_at"},
    "messages": {"id", "conversation_id", "direction", "kind", "content", "metadata_json", "status", "created_at"},
    "agent_state": {"id", "agent_id", "project_id", "state_json", "attempt_count", "created_at", "updated_at"},
    "experience_events": {"id", "project_id", "event_type", "metadata_json", "created_at"},
    "command_requests": {"id", "command_id", "project_id", "cwd", "command_json", "reason", "risk_level", "status", "requires_confirmation", "created_at"},
    "command_results": {"id", "command_request_id", "return_code", "stdout", "stderr", "files_changed_json", "diff_stat", "created_at"},
    "memories": {"id", "project_id", "scope", "category", "content", "importance", "confidence", "source_type", "created_at", "updated_at"},
    "lessons": {"id", "project_id", "problem", "root_cause", "lesson", "severity", "status", "created_at"},
    "rules": {"id", "scope", "name", "rule_text", "priority", "enabled", "status", "created_at", "updated_at"},
    "self_improvement_tasks": {"id", "project_id", "title", "problem", "proposed_solution", "target_files_json", "risk_level", "status", "created_at"},
    "code_changes": {"id", "task_id", "branch", "files_changed_json", "diff_summary", "validation_json", "created_at"},
    "db_migrations": {"id", "migration_name", "migration_sql", "rollback_sql", "status", "environment"},
    "evaluations": {"id", "project_id", "name", "kind", "target", "status", "command_json", "result_json", "created_at", "updated_at"},
}

def connect_memory_db(path=":memory:"):
 c=sqlite3.connect(path); c.execute("PRAGMA foreign_keys=ON"); return c
def apply_schema(conn):
 for name,spec in TABLES.items(): conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({spec})")
 conn.commit()
def table_names(conn):
 return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
def column_names(conn,table):
 return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
def assert_schema_ready(conn):
 missing=set(TABLES)-table_names(conn)
 if missing: raise AssertionError(f"missing tables: {sorted(missing)}")
 bad={t:sorted(cols-column_names(conn,t)) for t,cols in REQUIRED.items() if cols-column_names(conn,t)}
 if bad: raise AssertionError(f"missing columns: {bad}")

