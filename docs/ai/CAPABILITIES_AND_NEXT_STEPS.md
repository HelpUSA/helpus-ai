# AI capabilities and next steps

Current validated baseline: **Phase U - Local audit safety index**.

Latest validated commit:

- `076c495 test: add local audit safety index`

## What the AI already does

The local HelpUS AI workflow currently works as a safe, auditable, proposal-oriented assistant.

It can help with:

- project status review;
- diff review;
- file and documentation inspection;
- proposal summary review;
- proposal detail review;
- local admin audit support;
- smoke validation;
- explicit gateway-assisted patch, commit, and push workflows.

The admin local area already supports read-only visibility for status, diffs, proposal summaries, proposal details, detected proposal identifiers, normalized identifiers, encoded identifiers, detail endpoint preview, detail checklist, detail boundaries, result guidance, and detail request contract.

## Current safety posture

The app-level local workflow must remain:

- read-only where it inspects project data;
- proposal-oriented where it describes possible changes;
- human-directed for patches and commits;
- non-executing inside the application;
- non-approving inside the application;
- covered by repeatable smoke aliases.

Validated safety markers:

- `SMOKE_LOCAL_AUDIT_SAFETY_INDEX_OK`
- `SMOKE_LOCAL_DETAIL_SAFETY_ALIAS_OK`
- `SMOKE_LOCAL_DETAIL_UI_SAFETY_CONTRACT_OK`
- `SMOKE_LOCAL_EXECUTOR_ABSENT_OK`

Validated aliases:

- `npm run smoke:local-audit-safety`
- `npm run smoke:local-detail-safety`
- `npm run smoke:phase-u`
- `npm run smoke:phase-t`

## Recommended next steps

### Phase V: AI capabilities status panel

Add a read-only section in the admin local UI showing what the AI can do, what is blocked, the latest validated commit, and the latest safety smoke baseline.

### Phase W: structured proposal risk scoring

Give each proposal a structured review with objective, changed files, risk level, safety impact, rollback note, and required smokes.

### Phase X: CI safety workflow

Run the local audit safety smoke chain in CI so safety regressions fail before merge.

### Phase Y: multi-agent handoff docs

Standardize handoff information between chats and gateway runs: source, target, command ID, phase, baseline commit, final commit, smokes, and next safe action.

### Phase Z: patch proposal mode

Prepare auditable patch proposals without adding app-level execution. The patch can be reviewed, then applied only through explicit user-directed gateway workflow.


## Phase V implementation contract

Status: implemented.

Phase V adds the read-only `Capacidades da IA` panel to `frontend/src/app/admin/local/page.tsx`.

Validated commands:

- `python scripts/46_smoke_ai_capabilities_panel.py`
- `npm run smoke:phase-v`
- `npm run smoke:local-audit-safety`

Safety contract:

- no app-level execution;
- no app-level approval;
- no automatic detail fetch;
- patch, commit, and push remain explicit gateway or shell actions.

## Phase W: structured proposal risk scoring

Status: implemented.

Phase W adds a read-only structured proposal risk scoring panel to `frontend/src/app/admin/local/page.tsx`.

Validated contract:

- UI marker: `Matriz de risco estruturado`.
- Smoke alias: `npm run smoke:phase-w`.
- UI smoke: `python scripts/47_smoke_structured_proposal_risk_panel.py`.
- Safety chain preserved: `npm run smoke:phase-v` and `npm run smoke:local-audit-safety`.
- No app-level execution, approval, or automatic fetch is introduced.

The panel classifies loaded proposals/plans into readable risk states and shows required smokes plus rollback guidance.

## Phase X: CI safety workflow

Status: implemented.

Phase X adds a GitHub Actions workflow for the local audit safety smoke chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/48_smoke_ci_safety_workflow.py`

Validated contract:

- CI runs on `push` to `main`.
- CI runs on `pull_request`.
- CI uses read-only repository permissions.
- CI validates the workflow contract.
- CI runs `npm run smoke:phase-w`.

Local validation alias:

- `npm run smoke:phase-x`

The workflow does not add app-level execution, approval, or automatic patch behavior.

## Phase Y implementation contract

Status: implemented.

Phase Y adds the standardized multi-agent handoff protocol.

Files:

- `docs/ai/MULTI_AGENT_HANDOFF.md`
- `scripts/49_smoke_multi_agent_handoff_docs.py`

Validation:

- `python scripts/49_smoke_multi_agent_handoff_docs.py`
- `npm run smoke:phase-y`
- `npm run smoke:phase-x`

The protocol records the repository, branch, phase, base commit, final commit, changed files, validation results, safety posture, next action, and rollback guidance.

The application remains read-only, proposal-oriented, non-executing, and non-approving.

## Phase Z implementation contract

Status: implemented.

Phase Z adds a read-only patch proposal mode to `/admin/local`.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/50_smoke_patch_proposal_mode.py`

Validation:

- `python scripts/50_smoke_patch_proposal_mode.py`
- `npm run smoke:phase-z`
- `npm run smoke:phase-y`

The panel derives an auditable proposal preview from the loaded plan or proposal.

It does not apply patches, execute commands, create commits, perform pushes, or approve changes.

## Phase AA implementation contract

Status: implemented.

Phase AA updates the GitHub Actions safety workflow so CI also validates the complete Phase Z patch proposal chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/51_smoke_ci_phase_z_chain.py`

Validation:

- `python scripts/51_smoke_ci_phase_z_chain.py`
- `npm run smoke:phase-aa`
- `npm run smoke:phase-z`

The CI workflow retains read-only repository permissions and does not apply patches, approve proposals, create commits, or push changes.

## Phase AB implementation contract

Status: implemented.

Phase AB adds a read-only multi-agent handoff summary preview to `/admin/local`.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/52_smoke_handoff_summary_preview.py`

Validation:

- `python scripts/52_smoke_handoff_summary_preview.py`
- `npm run smoke:phase-ab`
- `npm run smoke:phase-aa`

The preview derives handoff text from the current patch proposal and structured risk state. It does not send messages, invoke another agent, execute commands, approve changes, create commits, or push code.

## Phase AC implementation contract

Status: implemented.

Phase AC adds explicit copy-to-clipboard support to the read-only handoff summary panel.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/53_smoke_handoff_copy_clipboard.py`

Validation:

- `python scripts/53_smoke_handoff_copy_clipboard.py`
- `npm run smoke:phase-ac`
- `npm run smoke:phase-ab`

Copying requires a user click. It does not transmit the handoff, contact another agent, execute commands, approve changes, create commits, or push code.

## Phase AD implementation contract

Status: implemented.

Phase AD updates the GitHub Actions workflow so CI validates the complete Phase AC handoff-copy safety chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/54_smoke_ci_phase_ac_chain.py`

Validation:

- `python scripts/54_smoke_ci_phase_ac_chain.py`
- `npm run smoke:phase-ad`
- `npm run smoke:phase-ac`

The workflow retains read-only repository permissions and does not transmit handoffs, execute commands, approve changes, create commits, or push code.

## Phase AE implementation contract

Status: implemented.

Phase AE adds an explicit local `.txt` download to the read-only handoff summary panel.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/55_smoke_handoff_download.py`

Validation:

- `python scripts/55_smoke_handoff_download.py`
- `npm run smoke:phase-ae`
- `npm run smoke:phase-ad`

The download requires a user click and creates only a local text file. It does not transmit the handoff, contact another agent, execute commands, approve changes, create commits, or push code.

## Phase AF implementation contract

Status: implemented.

Phase AF updates the GitHub Actions workflow so CI validates the complete Phase AE handoff-download safety chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/56_smoke_ci_phase_ae_chain.py`

Validation:

- `python scripts/56_smoke_ci_phase_ae_chain.py`
- `npm run smoke:phase-af`
- `npm run smoke:phase-ae`

The workflow retains read-only repository permissions and does not transmit handoffs, execute commands, approve changes, create commits, or push code.

## Phase AG implementation contract

Status: implemented.

Phase AG adds a read-only handoff readiness checklist to `/admin/local`.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/57_smoke_handoff_readiness_checklist.py`

Validation:

- `python scripts/57_smoke_handoff_readiness_checklist.py`
- `npm run smoke:phase-ag`
- `npm run smoke:phase-af`

The checklist verifies repository, branch, source, declared files, smoke chain, risk, safety posture, next action, and rollback. It does not approve, transmit, or execute the handoff.
