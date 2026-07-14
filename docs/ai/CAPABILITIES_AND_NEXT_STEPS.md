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

## Phase AH implementation contract

Status: implemented.

Phase AH updates GitHub Actions so CI validates the complete Phase AG handoff-readiness chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/58_smoke_ci_phase_ag_chain.py`

Validation:

- `python scripts/58_smoke_ci_phase_ag_chain.py`
- `npm run smoke:phase-ah`
- `npm run smoke:phase-ag`

The workflow retains read-only repository permissions and does not approve, transmit, or execute handoffs.

## Phase AI implementation contract

Status: implemented.

Phase AI adds a machine-readable JSON preview and explicit local JSON download to `/admin/local`.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/59_smoke_handoff_json_export.py`

Validation:

- `python scripts/59_smoke_handoff_json_export.py`
- `npm run smoke:phase-ai`
- `npm run smoke:phase-ah`

The export includes repository, branch, risk, changed files, validation, safety posture, next action, rollback, readiness, `humanReviewRequired: true`, `approved: false`, and `executed: false`.

The JSON remains local and is generated only after explicit user interaction.

## Phase AJ implementation contract

Status: implemented.

Phase AJ updates GitHub Actions so CI validates the complete Phase AI machine-readable handoff JSON chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/60_smoke_ci_phase_ai_chain.py`

Validation:

- `python scripts/60_smoke_ci_phase_ai_chain.py`
- `npm run smoke:phase-aj`
- `npm run smoke:phase-ai`

The workflow retains read-only repository permissions and does not approve, transmit, download, or execute handoffs.

## Phase AK implementation contract

Status: implemented.

Phase AK adds an explicit local SHA-256 fingerprint action to the read-only handoff JSON preview.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/61_smoke_handoff_fingerprint.py`

Validation:

- `python scripts/61_smoke_handoff_fingerprint.py`
- `npm run smoke:phase-ak`
- `npm run smoke:phase-aj`

The browser calculates the fingerprint locally only after an explicit click.

The fingerprint supports local integrity comparison. It is not a digital signature and does not approve, transmit, execute, commit, or push anything.

## Phase AL implementation contract

Status: implemented.

Phase AL updates GitHub Actions so CI validates the complete Phase AK local handoff-fingerprint chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/62_smoke_ci_phase_ak_chain.py`

Validation:

- `python scripts/62_smoke_ci_phase_ak_chain.py`
- `npm run smoke:phase-al`
- `npm run smoke:phase-ak`

The workflow retains read-only repository permissions and does not calculate browser fingerprints, approve, transmit, or execute handoffs.

## Phase AM implementation contract

Status: implemented.

Phase AM adds explicit local comparison between the currently generated handoff fingerprint and a SHA-256 value entered by the user.

Files:

- `frontend/src/app/admin/local/page.tsx`
- `scripts/63_smoke_handoff_fingerprint_comparison.py`

Validation:

- `python scripts/63_smoke_handoff_fingerprint_comparison.py`
- `npm run smoke:phase-am`
- `npm run smoke:phase-al`

The comparison requires a user click and reports only exact equality, divergence, missing current fingerprint, or invalid input.

It does not establish trust, approve, authorize, transmit, execute, commit, or push anything.

## Phase AN implementation contract

Status: implemented.

Phase AN updates GitHub Actions so CI validates the complete Phase AM explicit fingerprint-comparison chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/64_smoke_ci_phase_am_chain.py`

Validation:

- `python scripts/64_smoke_ci_phase_am_chain.py`
- `npm run smoke:phase-an`
- `npm run smoke:phase-am`

The workflow retains read-only repository permissions and does not compare browser values, establish trust, approve, authorize, transmit, or execute handoffs.

## Phase AO implementation contract

Status: implemented.

Phase AO replaces the project-oriented main sidebar with a flat and functional conversation navigator.

Capabilities:

- single searchable conversation list;
- reopening through the existing `/historico/{session_id}` contract;
- active conversation highlighting;
- refresh using `GET /conversas`;
- permanent deletion using `DELETE /conversa/{session_id}`;
- local browser aliases for conversation titles;
- copy-link support for every conversation;
- responsive mobile sidebar;
- account and operational-panel access;
- useful top actions menu;
- no simulated project grouping.

Validation:

- `python scripts/65_smoke_chat_sidebar_navigation.py`
- `npm run smoke:phase-ao`
- `npm run smoke:phase-an`

The sidebar does not introduce command execution, approval, automatic transmission, commits, or pushes.

## Phase AP implementation contract

Status: implemented.

Phase AP updates GitHub Actions so CI validates the complete Phase AO flat chat-navigation chain.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/66_smoke_ci_phase_ao_chain.py`

Validation:

- `python scripts/66_smoke_ci_phase_ao_chain.py`
- `npm run smoke:phase-ap`
- `npm run smoke:phase-ao`

The workflow retains read-only repository permissions.

It validates the conversation navigation contract without opening, creating, renaming, deleting, transmitting, approving, or executing conversations.

## Phase AQ implementation contract

Status: implemented.

Phase AQ improves the primary central chat experience.

Capabilities:

- automatic scrolling after messages and loading-state changes;
- explicit scroll-to-bottom control when the user moves away from the latest message;
- useful empty state with starter prompts;
- automatic composer height adjustment;
- explicit web-search toggle;
- response cancellation through AbortController;
- retry of the last submitted request without duplicating the user message;
- separate and dismissible error state;
- message reuse for user prompts;
- preserved assistant copy action;
- clearer loading and composer guidance.

Validation:

- `python scripts/67_smoke_chat_central_experience.py`
- `npm run smoke:phase-aq`
- `npm run smoke:phase-ap`
- frontend production build.

The feature does not introduce command execution, approval, automatic transmission, commits, or pushes from the browser.

## Phase AR implementation contract

Status: implemented.

Phase AR updates GitHub Actions so CI validates the complete Phase AQ central-chat experience.

Files:

- `.github/workflows/local-audit-safety.yml`
- `scripts/68_smoke_ci_phase_aq_chain.py`

Validation:

- `python scripts/68_smoke_ci_phase_aq_chain.py`
- `npm run smoke:phase-ar`
- `npm run smoke:phase-aq`

The workflow retains read-only repository permissions and performs only static and smoke validation.

## Phase AS implementation contract

Phase AS replaces the limited manual central-chat parser with safe Markdown rendering based on `react-markdown` and `remark-gfm`.

The implemented contract includes:

- assistant responses render headings, lists, blockquotes, inline code, fenced code, tables, links, task lists, separators, and strikethrough;
- user messages remain controlled plain text;
- raw HTML remains disabled through `skipHtml`;
- Markdown and source links accept only absolute HTTP or HTTPS URLs;
- external links use `noopener`, `noreferrer`, and `nofollow`;
- external Markdown images become protected links instead of loading automatically;
- fenced code blocks provide an explicit copy action;
- source cards display title, provider, hostname, numbering, and blocked-link guidance;
- no local execution or automatic approval endpoint is introduced.

Validation:

- `python scripts/69_smoke_chat_markdown_rendering.py`
- `npm run smoke:phase-as-ui`
- `npm run smoke:phase-as`
- `npm --prefix frontend run build`

Current validated product baseline after this checkpoint: Phase AS.

The next recommended phase is Phase AT, adding the complete Phase AS validation chain to GitHub Actions.

## Phase AT CI validation contract

Phase AT adds the complete Phase AS safe Markdown validation chain to the read-only GitHub Actions workflow.

The implemented contract includes:

- `scripts/70_smoke_ci_phase_as_chain.py`;
- exact `smoke:phase-at-ci` and `smoke:phase-at` aliases;
- cumulative validation through `AT -> AS -> AR -> AQ`;
- workflow validation for `contents: read`, Node.js 22, Python 3.12, the 15-minute timeout, and the existing conditional dependency installation;
- preservation of the current local read-only and proposal-only safety boundary;
- no local execution endpoint, automatic approval path, executor, or true `approved` or `executed` state.

Validation:

- `python scripts/70_smoke_ci_phase_as_chain.py`
- `npm run smoke:phase-at`
- `npm run smoke:phase-as`
- `npm run smoke:phase-ar`
- `python scripts/38_smoke_local_executor_absent.py`
- `python scripts/43_smoke_local_detail_ui_safety_contract.py`
- `npm run smoke:local-audit-safety`
- `npm --prefix frontend run build`

Current validated product baseline after this checkpoint: Phase AT.

The next product phase should be selected after the Phase AT workflow result is confirmed on `origin/main`.
