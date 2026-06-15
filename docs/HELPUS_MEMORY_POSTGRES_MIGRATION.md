# HelpUSAI Railway Postgres Memory Migration

Updated: 2026-06-15

## Purpose

Micro 31 prepares a reviewed, additive PostgreSQL migration for HelpUSAI persistent memory.

This micro does not apply the migration automatically.

## Files

- `migrations/helpus_memory_v1_postgres.sql`
- `scripts/railway/apply_helpus_memory_migration.py`
- `scripts/watcher/smoke_helpus_memory_postgres_migration_sql.py`
- `scripts/watcher/smoke_helpus_memory_migration_apply_guard.py`

## Tables

The migration creates these tables if they do not exist:

- `helpus_memory_events`
- `helpus_memory_feedback`
- `helpus_memory_lessons`
- `helpus_memory_rules`

## Safety

The SQL is additive only:

- no `drop table`
- no `delete from`
- no `truncate`
- no `alter table`
- no `update`

The apply script refuses to run unless this variable is set:

HELPUS_APPLY_MEMORY_MIGRATION=YES_APPLY_HELPUS_MEMORY_V1

## Review command

Set-Location "D:/dev/ai"
Get-Content migrations/helpus_memory_v1_postgres.sql
python scripts/watcher/smoke_helpus_memory_postgres_migration_sql.py
python scripts/watcher/smoke_helpus_memory_migration_apply_guard.py

## Future controlled apply

After review, the migration can be applied in Railway with environment variables available to the `helpus-api` service.

The apply step must be explicit and human-approved.

## Next step

Micro 32 should apply the migration in a controlled way and then run readonly table verification.
