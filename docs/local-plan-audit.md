# Local Plan Audit v1

Status: implemented for HelpUSAI Phase C preparation.

## Purpose

The audit layer records plan proposals before any future execution capability exists. It does not approve, schedule, run, or mutate commands.

## Endpoints

- `POST /local/plan/proposals`
- `GET /local/plan/proposals`

## Invariants

Every proposal record keeps:

- `mode = "proposal_only"`
- `version = "local-plan-audit-v1"`
- `executed = false`
- `approved = false`
- `approval_status = "pending_human_review"`
- `requires_human_confirmation = true`

## Storage

Proposal records are stored as JSON Lines in `reports/local-plan-proposals.jsonl`.

The smoke test redirects storage to a temporary file, so validation does not dirty the repository.

## Next gate

Before any execution is introduced, the project should add explicit human approval records, immutable audit entries, proposal-to-approval linking, and keep the executor disabled by default.

## Executor absence guard

The repository includes `scripts/38_smoke_local_executor_absent.py` to prevent accidental introduction of local execution endpoints before the human approval model is designed.

The smoke checks that:

- no `/local/execute`, `/local/commands`, `/local/plan/execute`, `/local/plan/run`, or approval endpoint exists;
- the audit module does not call `subprocess`, `os.system`, `Popen`, `check_call`, or `check_output`;
- proposal records keep `executed=false`, `approved=false`, and `approval_status=pending_human_review`.

## Phase D audit integrity

New proposal records include a canonical SHA-256 integrity envelope:

- `integrity_version = "local-plan-audit-integrity-v1"`
- `integrity_algorithm = "sha256-json-v1"`
- `previous_record_hash`
- `record_hash`

The read-only endpoint `GET /local/plan/proposals/verify` verifies stored proposal rows without approving or executing anything. It reports checked rows, legacy rows, and integrity errors.

The integrity layer remains proposal-only. It does not add approval endpoints, execution endpoints, subprocess calls, schedulers, or command runners.

## Phase E admin integrity UI

The admin local read-only panel now exposes the proposal integrity check through a UI action named `Verificar integridade auditavel`.

The UI calls `GET /local/plan/proposals/verify` and displays the JSON result under `Resultado da integridade`. This remains read-only and does not add approval, execution, scheduling, subprocess calls, or command runners.

## Phase F verify API contract

The verify endpoint now has a dedicated regression smoke for its read-only contract:

- `scripts/40_smoke_local_plan_verify_api_contract.py`
- `npm run smoke:phase-f-verify-api`
- `npm run smoke:phase-f`

The smoke guards that `GET /local/plan/proposals/verify` delegates to `verify_local_plan_proposal_integrity`, is not exposed through mutating HTTP methods, returns `proposal_only` integrity data, and does not mutate the local proposal store.

## Phase G summary API contract

The proposal audit module now exposes a read-only summary helper and API:

- `summarize_local_plan_proposals(limit=200)`
- `GET /local/plan/proposals/summary`
- `scripts/41_smoke_local_plan_summary_api_contract.py`
- `npm run smoke:phase-g-summary-api`
- `npm run smoke:phase-g`

The summary reports counts by intent, creator, approval status, and mode. It also surfaces the latest proposal and record hash without mutating the proposal store or adding any executor or approval path.

## Phase H summary UI contract

The admin local panel now exposes the proposal summary API through a read-only UI block:

- Carregar resumo auditavel
- Resumo auditavel
- GET /local/plan/proposals/summary?limit=200
- scripts/helpusai/smoke_admin_local_audit_summary_panel.py
- npm run smoke:phase-h-ui
- npm run smoke:phase-h

The UI only fetches and renders the summary JSON. It does not add any executor, run, command, or approval path.


## Phase I detail API contract

The local proposal audit layer now exposes a read-only detail API for a single stored proposal:

- `GET /local/plan/proposals/{proposal_id}`
- `get_local_plan_proposal(proposal_id)`
- `scripts/42_smoke_local_plan_detail_api_contract.py`
- `npm run smoke:phase-i-detail-api`
- `npm run smoke:phase-i`

The endpoint only reads the JSONL proposal store and returns `found=true` with the matching proposal or `found=false` with `proposal=null`. It does not add any executor, run, command, mutation, or approval path.

## Phase J: Detail UI read-only

A UI administrativa em `/admin/local` agora consegue consultar uma proposta auditavel especifica em modo read-only.

Contrato preservado:

- Campo `proposal_id para detalhe auditavel`.
- Botao `Carregar detalhe auditavel`.
- Chamada GET para `/local/plan/proposals/{proposal_id}`.
- Bloco `Detalhe da proposta` para exibir o JSON retornado.
- Sem executar comando, aprovar proposta ou criar endpoint de execucao.
- Smoke: `npm run smoke:phase-j-ui`.
- Cadeia: `npm run smoke:phase-j`.

## Phase K: Detail quick-fill UI read-only

The admin local read-only panel now includes a convenience layer for proposal detail lookup.

Preserved contract:

- Button `Preencher id da proposta criada` extracts `proposal_id` from the last created proposal response.
- Button `Preencher id da lista` extracts `proposal_id` from the listed proposals response.
- Both actions only fill the existing `proposal_id para detalhe auditavel` input.
- The existing `Carregar detalhe auditavel` action remains the only detail fetch and uses GET `/local/plan/proposals/{proposal_id}`.
- No execution endpoint, approval endpoint, or command runner is added.
- Smoke: `npm run smoke:phase-k-ui`.
- Chain: `npm run smoke:phase-k`.

## Phase L: Detected proposal_id hint UI read-only

The admin local read-only panel now shows `proposal_id detectado automaticamente`, derived only from existing UI state with `findProposalId(proposalResult) || findProposalId(proposals)`. It does not fetch, approve, mutate, or execute. Smoke: `npm run smoke:phase-l-ui`; chain: `npm run smoke:phase-l`.

## Phase M: Endpoint preview UI read-only

The admin local read-only panel now shows a non-mutating detail endpoint preview labeled `Preview GET detalhe auditavel`.

Preserved contract:

- The preview derives only from `proposalDetailId.trim()`.
- It renders `/local/plan/proposals/{proposal_id}` until an id is present.
- When an id is present, it renders `/local/plan/proposals/${encodeURIComponent(proposalDetailId.trim())}`.
- It does not fetch automatically, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-m-ui`.
- Chain: `npm run smoke:phase-m`.

## Phase N: Detail proposal_id status UI read-only

The admin local read-only panel now shows a non-mutating detail id status block labeled `Status do proposal_id para detalhe`.

Preserved contract:

- The status reads only from `proposalDetailId.trim()`.
- It shows `Pronto para consulta GET read-only.` when an id is present.
- It shows `Informe ou preencha um proposal_id antes de carregar o detalhe.` when the field is empty.
- It does not fetch automatically, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-n-ui`.
- Chain: `npm run smoke:phase-n`.

## Phase O: Detail normalized proposal_id UI read-only

The admin local read-only panel now shows a non-mutating normalized detail id block labeled `proposal_id normalizado para detalhe`.

Preserved contract:

- The normalized value reads only from `proposalDetailId.trim()`.
- It shows `Nenhum proposal_id informado.` while the detail id field is empty.
- It does not fetch automatically, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-o-ui`.
- Chain: `npm run smoke:phase-o`.

## Phase P: Detail encoded proposal_id UI read-only

The admin local read-only panel now shows a non-mutating encoded detail id block labeled `proposal_id codificado para endpoint de detalhe`.

Preserved contract:

- The encoded value reads only from `proposalDetailId.trim()`.
- It shows `Nenhum proposal_id para codificar.` while the detail id field is empty.
- It uses `encodeURIComponent(proposalDetailId.trim())` only for display.
- It does not fetch automatically, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-p-ui`.
- Chain: `npm run smoke:phase-p`.

## Phase Q: Detail GET checklist UI read-only

The admin local read-only panel now shows a non-mutating detail GET checklist block labeled `Checklist GET detalhe auditavel`.

Preserved contract:

- The checklist is static/read-only guidance for the detail lookup flow.
- It reminds the user to confirm the normalized proposal id, check the encoded proposal id, review the preview endpoint, and only then click `Carregar detalhe auditavel`.
- It does not fetch automatically, fill fields, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-q-ui`.
- Chain: `npm run smoke:phase-q`.

## Phase R: Detail GET boundary UI read-only

The admin local read-only panel now shows a non-mutating detail GET boundary block labeled `Limite da consulta GET de detalhe`.

Preserved contract:

- The block is static/read-only guidance for the detail lookup flow.
- It states that status, normalization, encoding, checklist, and preview blocks are read-only.
- It states that the detail GET lookup happens only when the user clicks `Carregar detalhe auditavel`.
- It does not fetch automatically, fill fields, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-r-ui`.
- Chain: `npm run smoke:phase-r`.

## Phase R: Detail result guide UI read-only

The admin local read-only panel now shows a non-mutating result guide block labeled `Guia do resultado do detalhe`.

Preserved contract:

- The guide is static/read-only guidance for interpreting detail lookup results.
- It explains `found`, `proposal`, and the safety expectation that `executed` and `approved` remain false.
- It does not fetch automatically, fill fields, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-r-ui`.
- Chain: `npm run smoke:phase-r`.

## Phase R: Detail GET contract UI read-only

The admin local read-only panel now shows a non-mutating detail GET contract block labeled `Contrato GET detalhe auditavel`.

Preserved contract:

- The contract block is static/read-only guidance for the detail lookup flow.
- It documents the allowed endpoint shape as `GET /local/plan/proposals/[proposal_id]`.
- It states that the lookup is read-only and does not create, approve, or execute proposals.
- It does not fetch automatically, fill fields, create proposals, approve proposals, mutate audit records, or execute commands.
- Smoke: `npm run smoke:phase-r-ui`.
- Chain: `npm run smoke:phase-r`.

## Phase S: Detail safety aggregate smoke

The local admin audit panel now has an aggregate safety smoke for the detail lookup guidance surface.

Preserved contract:

- Smoke: `python scripts/43_smoke_local_detail_ui_safety_contract.py`.
- Chain: `npm run smoke:phase-s`.
- The smoke verifies the detail read-only guidance markers from phases J through R.
- It checks the guidance blocks remain free of proposal execution, approval, unsafe local command endpoints, automatic POSTs, and field mutations.
- It does not add any endpoint, executor, approval path, or automatic detail fetch.

## Phase T: Detail safety smoke alias

The local admin audit detail safety checks now have a direct smoke alias named `smoke:local-detail-safety`.

Preserved contract:

- Alias: `npm run smoke:local-detail-safety`.
- The alias runs the aggregate detail UI safety contract plus the executor absence guard.
- Phase chain: `npm run smoke:phase-t`.
- Validation smoke: `python scripts/44_smoke_local_detail_safety_alias.py`.
- It does not add any endpoint, executor, approval path, or automatic detail fetch.

## Phase U: Local audit safety index

The local admin audit safety checks now include a stable index smoke named `smoke:local-audit-safety`.

Preserved contract:

- Alias: `npm run smoke:local-audit-safety`.
- Phase chain: `npm run smoke:phase-u`.
- Validation smoke: `python scripts/45_smoke_local_audit_safety_index.py`.
- The index validates the Phase T detail safety alias, the aggregate detail UI safety contract, and the executor absence guard.
- It does not add any endpoint, executor, approval path, or automatic detail fetch.

## AI capability summary after Phase U

Phase U is the current validated baseline for local audit safety.

Current validated commit: `076c495 test: add local audit safety index`.

Current safety aliases:

- `npm run smoke:local-audit-safety`
- `npm run smoke:local-detail-safety`
- `npm run smoke:phase-u`
- `npm run smoke:phase-t`

The local AI workflow can assist with status review, diff review, file inspection, documentation search, proposal summaries, proposal details, local admin audit review, smoke validation, and explicit gateway-assisted patch workflows.

The app-level local workflow remains read-only, proposal-oriented, non-executing, and non-approving.

Expanded capability and roadmap notes are in `docs/ai/CAPABILITIES_AND_NEXT_STEPS.md`.

## AI capabilities panel after Phase V

The admin local page now includes a read-only AI capabilities panel.

It shows:

- active read-only inspection capabilities;
- active proposal and detail review capabilities;
- blocked app-level execution and approval behavior;
- validated smoke aliases including `smoke:phase-v` and `smoke:local-audit-safety`.

Validation smoke: `python scripts/46_smoke_ai_capabilities_panel.py`.

## Structured proposal risk scoring after Phase W

The admin local page now includes a read-only structured risk panel for proposal and plan review.

It shows:

- derived risk level;
- required smoke aliases;
- rollback suggestion;
- risk justification.

Validation smoke: `python scripts/47_smoke_structured_proposal_risk_panel.py`.
Alias: `npm run smoke:phase-w`.

## CI safety workflow after Phase X

The project now includes a GitHub Actions safety workflow for local audit checks.

Workflow:

- `.github/workflows/local-audit-safety.yml`

Local smoke:

- `python scripts/48_smoke_ci_safety_workflow.py`
- `npm run smoke:phase-x`

The workflow validates the current read-only local audit safety chain through `npm run smoke:phase-w`.

## Multi-agent handoff docs after Phase Y

The project now includes `docs/ai/MULTI_AGENT_HANDOFF.md`.

Validation:

- `python scripts/49_smoke_multi_agent_handoff_docs.py`
- `npm run smoke:phase-y`

## Patch proposal mode after Phase Z

The admin local page now includes a read-only patch proposal preview.

It shows proposal-only mode, review status, objective, declared files, required smokes, rollback guidance, and an auditable JSON preview.

Validation:

- `python scripts/50_smoke_patch_proposal_mode.py`
- `npm run smoke:phase-z`

## Phase Z CI chain after Phase AA

The GitHub Actions workflow now validates the complete Phase Z safety chain.

Validation:

- `python scripts/51_smoke_ci_phase_z_chain.py`
- `npm run smoke:phase-aa`
- `npm run smoke:phase-z`

The previous Phase X and Phase W checks remain present for backward contract validation.

## Handoff summary preview after Phase AB

The admin local page now shows a read-only handoff summary derived from the loaded patch proposal and structured risk state.

Validation:

- `python scripts/52_smoke_handoff_summary_preview.py`
- `npm run smoke:phase-ab`

## Handoff copy support after Phase AC

The read-only handoff preview can now be copied to the local clipboard through an explicit button.

Validation:

- `python scripts/53_smoke_handoff_copy_clipboard.py`
- `npm run smoke:phase-ac`

No automatic transmission or execution is introduced.

## Phase AC CI chain after Phase AD

The GitHub Actions safety workflow now validates the complete Phase AC handoff-copy chain.

Validation:

- `python scripts/54_smoke_ci_phase_ac_chain.py`
- `npm run smoke:phase-ad`
- `npm run smoke:phase-ac`

## Handoff download after Phase AE

The local admin handoff preview can now be downloaded as `helpusai-handoff.txt`.

Validation:

- `python scripts/55_smoke_handoff_download.py`
- `npm run smoke:phase-ae`

The download remains local and requires an explicit user click.
