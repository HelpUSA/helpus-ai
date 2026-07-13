# Multi-agent handoff protocol

Current baseline: Phase X CI safety workflow.

## Purpose

This protocol standardizes handoffs between ChatGPT chats, agents, gateway runs, watcher operations, and shell scripts.

It does not authorize execution or approval inside the application.

## Required handoff fields

- repo
- local_path
- branch
- phase
- base_commit
- final_commit
- command_id or script_id
- operator
- changed_files
- validation
- safety_posture
- next_action
- rollback

## Successful handoff template

HANDOFF_START
repo=HelpUSA/helpus-ai
local_path=D:/dev/ai
branch=main
phase=<phase>
base_commit=<commit before work>
final_commit=<commit after push>
script_id=<script identifier>
operator=<ChatGPT|gateway|watcher|shell>
changed_files=<intended files>
validation=<commands and successful markers>
safety_posture=read-only/proposal-oriented/non-executing/non-approving inside app
next_action=<next safe action>
rollback=<revert or restore guidance>
HANDOFF_END

## Failed handoff template

HANDOFF_FAILURE_START
repo=HelpUSA/helpus-ai
local_path=D:/dev/ai
branch=main
phase=<phase>
base_commit=<commit before work>
script_id=<script identifier>
status=failed
failed_command=<command>
error_summary=<cause>
dirty_files=<expected dirty files>
safe_fix=<smallest safe correction>
rollback=<restore guidance>
HANDOFF_FAILURE_END

## Shell cadence

1. Confirm the branch and working tree.
2. Reject unexpected dirty files.
3. Apply one bounded patch.
4. Run the new phase smoke.
5. Run the previous safety chain.
6. Run git diff --check.
7. Commit only intended files.
8. Push to origin main.
9. Confirm a clean synchronized tree.
10. Record the final commit.

## Gateway and watcher cadence

1. Use a unique command identifier.
2. Keep source, target, and conversation context explicit.
3. Treat queued events as non-final.
4. Continue only after the final run result.
5. On success, record files, smokes, commit, and next action.
6. On failure, apply the smallest safe correction.

## Safety checklist

- working tree clean after completion;
- main synchronized with origin/main;
- dedicated phase smoke passed;
- previous safety chain passed;
- docs, status, and roadmap updated;
- no application-level execution;
- no application-level automatic approval;
- no automatic proposal-detail fetch.

## Current phase ladder

- Phase U: local audit safety index.
- Phase V: AI capabilities panel.
- Phase W: structured proposal risk scoring.
- Phase X: CI safety workflow.
- Phase Y: multi-agent handoff docs.

Next recommended phase: Phase Z patch proposal mode.

## Admin handoff summary preview after Phase AB

The local admin page now provides a read-only preview following the `HANDOFF_START` and `HANDOFF_END` format.

Validation:

- `python scripts/52_smoke_handoff_summary_preview.py`
- `npm run smoke:phase-ab`

The preview does not transmit the handoff automatically.

## Copy-to-clipboard after Phase AC

The admin handoff preview now includes an explicit `Copiar handoff` button.

Validation:

- `python scripts/53_smoke_handoff_copy_clipboard.py`
- `npm run smoke:phase-ac`

The action only copies text to the local clipboard after a user click. It does not transmit or execute the handoff.
