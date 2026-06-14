# HelpUS AI - Watcher operations runbook

Purpose: define safe day-to-day operation for HelpUS AI after completion of Micros 24 to 29. This is an operations guide, not a deploy command.

## Operating principle
All execution continues through watcher / AI Bridge Local. The assistant should inspect before patching, validate before committing, and never treat watcher receipts as new user commands.

## Standard work loop
1. Inspect repo state with git status -sb, git log, git diff --stat and git diff --check.
2. Read the relevant files before changing them.
3. Patch only the files required for the current micro or issue.
4. Run py_compile for touched Python files.
5. Run the dedicated smoke for the touched feature.
6. Run smoke_operational_release and smoke_health_report.
7. Run npm --prefix frontend run build when frontend or full readiness is involved.
8. Run git diff --check.
9. Commit only expected files.
10. Push only after all validations pass.

## Receipt handling
- AI_LOCAL means delivery receipt.
- AI_LOCAL_RUN with return_code=0 means command finished successfully.
- AI_LOCAL_RUN with return_code other than 0 means command executed and may have partial changes. Inspect before fixing.
- AI_LOCAL_ERRO with envelope_parse_error means nothing executed. Create a new command_id and simplify the envelope.
- Do not copy a failed envelope blindly.

## Failure playbooks
### envelope_parse_error
- Assume nothing executed.
- Create a new command_id.
- Use shorter ASCII-only JSON.
- Prefer small command arrays or a simple script_text only when supported.

### Python syntax or indentation failure
- Inspect git status and the broken file.
- Patch only the broken file.
- Run py_compile before any broader validation.

### Smoke failure
- Inspect the failing smoke output.
- Read the smoke and target module.
- Patch narrowly.
- Run the specific smoke before the full suite.

### Frontend build failure
- Inspect build output.
- Do not change backend files unless directly related.
- Re-run npm --prefix frontend run build after the fix.

### Dirty repo before work
- Do not start a new patch.
- Inspect git status, git diff --stat and git diff.
- Decide whether to continue, commit, or ask for explicit human decision if there is risk.

## Forbidden without explicit authorization
- deploy
- tag or release creation
- git reset --hard
- git clean
- mass deletion or mass moves
- printing or editing secrets
- destructive database operations

## Current stable baseline
- Final completion commit: f8b29c2 Add HelpUS final completion report.
- Release checklist commit: f197528 Add HelpUS release deploy checklist.
- Micros 24 to 29 are complete.
- Local AI provider is disabled by default and analysis_only.
- No deploy or tag has been executed.
