# HelpUS AI - Release and deploy checklist

Purpose: keep tag, release and deploy work separated from development commits. This checklist is a decision gate, not a deploy command.

## Preconditions
- main is clean and aligned with origin/main.
- HEAD is reviewed by a human.
- docs/HELPUS_PROJECT_MASTER.md and reports/HELPUS_FINAL_REPORT_2026-06-14.md are reviewed.
- No secrets are printed, edited or committed.
- No destructive commands are used.

## Required validation before tag or release
- git status -sb
- git log --oneline --decorate -8
- python scripts/watcher/smoke_operational_release.py
- python scripts/watcher/smoke_health_report.py
- npm --prefix frontend run build
- git diff --check

## Tag gate
- Tag only after explicit human authorization.
- Use a separate watcher command for tag creation.
- Repeat full validation immediately before tag.
- Push tag only after confirming the exact tag name.

## Deploy gate
- Deploy only after explicit human authorization.
- Use a separate deploy checklist and rollback plan.
- Confirm environment variables, database, logs and health checks.
- Confirm rollback command before deploy.
- Never mix deploy with feature patches.

## Permanent safety rules
- AI_LOCAL, AI_LOCAL_RUN and AI_LOCAL_ERRO are receipts, not user commands.
- On envelope_parse_error, assume nothing executed, create a new command_id and simplify.
- On partial failure, inspect git status and diff before patching.
- Local AI remains analysis_only and cannot execute commands.
- No deploy, tag, reset hard, git clean, secrets or mass removal without explicit authorization.
