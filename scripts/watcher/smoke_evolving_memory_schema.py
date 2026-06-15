from __future__ import annotations
from pathlib import Path
import sqlite3, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"backend"))
from evolving_memory_schema import apply_schema, assert_schema_ready, connect_memory_db, TABLES

def one(conn,sql,args=()):
 conn.execute(sql,args)

def main():
 conn=connect_memory_db()
 apply_schema(conn)
 assert_schema_ready(conn)
 one(conn,"INSERT INTO agents (id,name,role) VALUES (?,?,?)",("agent-1","supervisor","supervisor"))
 one(conn,"INSERT INTO conversations (id,title,project_id) VALUES (?,?,?)",("conv-1","micro1","helpus-ai"))
 one(conn,"INSERT INTO messages (id,conversation_id,source_agent_id,target_agent_id,direction,kind,content) VALUES (?,?,?,?,?,?,?)",("msg-1","conv-1","agent-1","agent-1","inbound","agent_message","ok"))
 one(conn,"INSERT INTO agent_state (id,agent_id,project_id,state_json) VALUES (?,?,?,?)",("state-1","agent-1","helpus-ai","{}"))
 one(conn,"INSERT INTO experience_events (id,project_id,agent_id,event_type) VALUES (?,?,?,?)",("event-1","helpus-ai","agent-1","command_failed"))
 one(conn,"INSERT INTO command_requests (id,command_id,requested_by_agent_id,project_id,cwd,command_json,reason,risk_level,requires_confirmation) VALUES (?,?,?,?,?,?,?,?,?)",("req-1","cmd-1","agent-1","helpus-ai","D:/dev/ai","[]","readonly","low",0))
 one(conn,"INSERT INTO command_results (id,command_request_id,return_code) VALUES (?,?,?)",("res-1","req-1",0))
 one(conn,"INSERT INTO memories (id,agent_id,project_id,scope,category,content,source_type) VALUES (?,?,?,?,?,?,?)",("mem-1","agent-1","helpus-ai","project","lesson","small micros","test"))
 one(conn,"INSERT INTO lessons (id,project_id,trigger_event_id,problem,root_cause,lesson,severity) VALUES (?,?,?,?,?,?,?)",("lesson-1","helpus-ai","event-1","problem","cause","lesson","medium"))
 one(conn,"INSERT INTO rules (id,scope,name,rule_text,source_lesson_id) VALUES (?,?,?,?,?)",("rule-1","repo","smoke-first","Use smoke first","lesson-1"))
 one(conn,"INSERT INTO self_improvement_tasks (id,project_id,title,problem,proposed_solution,risk_level,created_by_agent_id) VALUES (?,?,?,?,?,?,?)",("task-1","helpus-ai","task","problem","solution","low","agent-1"))
 one(conn,"INSERT INTO code_changes (id,task_id,branch,diff_summary) VALUES (?,?,?,?)",("change-1","task-1","main","summary"))
 one(conn,"INSERT INTO db_migrations (id,task_id,migration_name,migration_sql,rollback_sql) VALUES (?,?,?,?,?)",("mig-1","task-1","micro1","SELECT 1","SELECT 1"))
 one(conn,"INSERT INTO evaluations (id,project_id,name,kind,target) VALUES (?,?,?,?,?)",("eval-1","helpus-ai","smoke_evolving_memory_schema","smoke","schema"))
 conn.commit()
 for table in TABLES:
  got=conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
  if got!=1: raise AssertionError(f"{table} count {got}")
 try:
  one(conn,"INSERT INTO command_results (id,command_request_id,return_code) VALUES (?,?,?)",("orphan","missing",1))
 except sqlite3.IntegrityError:
  pass
 else:
  raise AssertionError("orphan command_result was accepted")
 try:
  one(conn,"INSERT INTO memories (id,project_id,scope,category,content,confidence,source_type) VALUES (?,?,?,?,?,?,?)",("bad","helpus-ai","project","fact","bad",2.0,"test"))
 except sqlite3.IntegrityError:
  pass
 else:
  raise AssertionError("bad confidence was accepted")
 print("EVOLVING_MEMORY_SCHEMA_SMOKE_OK")
if __name__=="__main__":
 main()
