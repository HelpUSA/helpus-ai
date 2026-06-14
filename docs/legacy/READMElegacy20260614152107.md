# HelpUS AI - Documentation index

This folder contains the active documentation for the completed HelpUS AI watcher intelligence cycle. Historical documents are preserved in docs/legacy.

## Active documents
- HELPUS_PROJECT_MASTER.md - master project status and roadmap.
- HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md - release, tag and deploy decision gate.
- HELPUS_WATCHER_OPERATIONS_RUNBOOK.md - safe watcher operations runbook.
- HELPUS_POST_COMPLETION_BACKLOG.md - future work backlog after completion.

## Versioned reports
- ../reports/HELPUS_FINAL_REPORT_2026-06-14.md - final completion report.

## Current baseline
- Micros 24 to 29 are complete.
- Execution remains via watcher / AI Bridge Local.
- Local AI is analysis_only and disabled by default.
- No deploy or tag has been executed.

## Rules
- Inspect before patching.
- Validate before committing.
- Treat AI_LOCAL, AI_LOCAL_RUN and AI_LOCAL_ERRO as receipts.
- Do not deploy, tag, reset hard, git clean, print secrets or do mass removals without explicit authorization.
