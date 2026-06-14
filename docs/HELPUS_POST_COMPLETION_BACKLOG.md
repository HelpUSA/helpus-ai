# HelpUS AI - Post completion backlog

Purpose: keep future work explicit and separated from the completed Micros 24 to 29 cycle. This backlog is planning only and does not authorize deploy, tag, release, destructive operations or secret changes.

## Completed baseline
- Micros 24 to 29 are complete.
- Final report is tracked in reports/HELPUS_FINAL_REPORT_2026-06-14.md.
- Release and deploy checklist is tracked in docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md.
- Watcher operations runbook is tracked in docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md.
- Current baseline after operations runbook: 6ce1e01 Add HelpUS watcher operations runbook.

## Priority 1 - Release readiness without deploy
- Re-run full validation on a clean repo.
- Review docs/HELPUS_PROJECT_MASTER.md.
- Review reports/HELPUS_FINAL_REPORT_2026-06-14.md.
- Decide whether to create a formal release tag in a separate authorized flow.
- No tag is created by this backlog.

## Priority 2 - Production deploy preparation
- Review docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md.
- Create or review production deploy runbook before any deploy.
- Confirm rollback plan and health checks.
- Confirm secrets without printing values.
- No deploy is executed by this backlog.

## Priority 3 - Operational hardening
- Add more receipt fixtures for AI_LOCAL_RUN and AI_LOCAL_ERRO cases.
- Expand watcher recovery fixtures for parse errors, build failures and smoke failures.
- Add regression checks for command_id uniqueness.
- Add documentation examples for safe watcher envelopes.

## Priority 4 - Product and UX follow up
- Review admin telemetry visibility.
- Review health report UX and location.
- Review local AI analysis-only toggle messaging.
- Review onboarding instructions for future maintainers.

## Always prohibited without explicit authorization
- deploy
- tag or release creation
- git reset --hard
- git clean
- mass deletion or mass move
- printing or editing secrets
- destructive database operation
