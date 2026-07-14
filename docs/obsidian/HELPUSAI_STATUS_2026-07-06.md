# HelpUSAI Status - 2026-07-06

## Checkpoint: Fase A Local Readonly API

A Fase A ganhou um checkpoint operacional importante: a API local read-only agora cobre status, diff, leitura de arquivo, listagem segura de arquivos e busca segura em documentos locais.

### Endpoints confirmados

- `GET /local/status`
- `GET /local/diff`
- `GET /local/files/read`
- `GET /local/files/list`
- `GET /local/docs/search`

### Commits relacionados

- `7a23006` - `test: add local readonly API smoke`
- `1fef2e4` - `test: add operational lessons full flow smoke`
- `56be358` - `test: keep Obsidian smoke isolated`
- `ddd57bd` - `feat: add local readonly file list and search`

### Validacoes executadas no checkpoint `ddd57bd`

- `python -m py_compile backend/main.py backend/local_readonly_files.py backend/local_repo_status.py scripts/34_smoke_local_readonly_api.py`
- `python scripts/34_smoke_local_readonly_api.py`
- `npm run smoke:local-api`
- `npm run build`
- `git diff --check`

### Garantias de seguranca mantidas

- Apenas caminhos allowlisted sao aceitos: `docs/`, `reports/`, `scripts/watcher/`, `backend/`.
- Caminhos absolutos e traversal sao bloqueados.
- Arquivos e caminhos com marcadores sensiveis sao bloqueados.
- Listagem e busca retornam apenas arquivos locais considerados seguros.
- Smoke cobre leitura permitida, path traversal, path fora da allowlist, marcador sensivel, listagem e busca.

### Estado operacional

- Branch: `main`
- Push confirmado para `origin/main`
- Worktree estava limpo apos o push de `ddd57bd`

### Proximo passo recomendado

Avancar para uma camada de consumo interno desses endpoints pelo operador/agente, mantendo a mesma politica: primeiro read-only, depois planejamento seguro, e somente depois execucao controlada.

## Checkpoint: UI Admin Local Readonly

A Fase A tambem ganhou uma interface administrativa isolada para consumir os endpoints locais read-only.

### UI adicionada

- Rota frontend: `/admin/local`
- Link de descoberta a partir de `/admin`
- Painel consulta apenas endpoints read-only:
  - `/local/status`
  - `/local/diff`
  - `/local/files/list?path=docs/`
  - `/local/docs/search?q=HelpUS AI&path=docs/`

### Smokes adicionados

- `scripts/helpusai/smoke_admin_local_readonly_panel.py`
- `scripts/helpusai/smoke_admin_local_readonly_link.py`
- `npm run smoke:admin-local`

### Commits relacionados

- `adf140f` - `feat: add admin local readonly panel`
- `7538598` - `feat: link admin to local readonly panel`
- `97a75a1` - `test: add admin local readonly smoke script`

### Validacoes executadas

- `npm run smoke:admin-local`
- `npm run smoke:local-api`
- `npm run build`
- `git diff --check`

### Estado operacional

O operador local read-only agora pode ser acessado pela UI administrativa sem alterar a pagina principal de admin e sem introduzir acoes destrutivas.

## Checkpoint: Validacao Consolidada da Fase A

A Fase A agora possui um comando unico de validacao operacional.

### Script oficial

- `npm run smoke:phase-a`

### O que ele executa

- `npm run smoke:local-api`
- `npm run smoke:admin-local`
- `npm run build`

### Commit relacionado

- `c2e1018` - `test: add phase A validation script`

### Estado operacional

Este comando valida o conjunto atual da Fase A: API local read-only, painel admin `/admin/local`, link no `/admin`, smokes dedicados e build Next.js.

### Uso recomendado

Rodar `npm run smoke:phase-a` antes de qualquer evolucao para Fase B ou antes de diagnosticar regressao no operador local read-only.

## Checkpoint: Fase B Plan-only API

A Fase B foi iniciada com um endpoint de planejamento seguro que nao executa comandos.

### Endpoint adicionado

- `POST /local/plan`

### Garantias

- Modo sempre `plan_only`.
- Campo `executed` sempre `false`.
- Comandos destrutivos sao classificados como bloqueados.
- Comandos fora da allowlist read-only exigem revisao humana.
- Mesmo planos permitidos exigem confirmacao humana antes de qualquer execucao futura.

### Script oficial

- `npm run smoke:phase-b-plan`

### Validacoes do checkpoint

- `python -m py_compile backend/main.py backend/local_safe_plan.py scripts/35_smoke_local_safe_plan.py`
- `python scripts/35_smoke_local_safe_plan.py`
- `npm run smoke:phase-b-plan`
- `npm run smoke:phase-a`
- `npm run build`
- `git diff --check`

### Estado operacional

A AI-HelpUS agora consegue propor planos locais seguros em modo read-only/plan-only, mas ainda nao executa comandos. Isso prepara a ponte entre diagnostico da Fase A e execucao controlada futura.

## Checkpoint: Fase B Plan-only UI

O endpoint `POST /local/plan` agora aparece na UI `/admin/local`.

### UI adicionada

- Secao `Planejamento seguro` no operador local.
- Plano permitido de exemplo: `phase_a_validation`.
- Plano bloqueado de exemplo: `git push origin main`.
- A UI mostra explicitamente que nenhum comando e executado.

### Scripts oficiais

- `npm run smoke:phase-b-ui`
- `npm run smoke:phase-b`

### Garantias

- UI apenas consulta o planner.
- Planner continua retornando `executed=false`.
- Exemplo bloqueado valida visualmente a politica contra comandos destrutivos.

### Proxima direcao

Adicionar campos controlados para o usuario solicitar planos customizados, ainda sem execucao automatica.

## Checkpoint: Fase B Custom Planner Contract

Contrato `local-plan-v1` adicionado com `GET /local/plan/intents`, limites de comando, bloqueio de chaining, intent `phase_b_validation`, intent `local_recent_commits` e documento `docs/local-plan-contract.md`. A execuÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o segue desabilitada.

## Checkpoint: Fase C Audit Proposal Queue

Criada camada de auditoria proposal-only antes de qualquer execuÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o real.

Escopo entregue:

- `backend/local_plan_audit.py`
- `POST /local/plan/proposals`
- `GET /local/plan/proposals`
- `scripts/37_smoke_local_plan_audit.py`
- `docs/local-plan-audit.md`
- `npm run smoke:phase-c-audit`
- `npm run smoke:phase-c`

Invariantes mantidas: `executed=false`, `approved=false`, `approval_status=pending_human_review` e executor ainda inexistente/desabilitado.

## Checkpoint: Fase C Audit UI

Adicionado painel em `/admin/local` para registrar e listar propostas auditaveis sem execucao real.

Escopo:
- secao `Propostas auditaveis`
- botao `Criar proposta auditavel sem executar`
- botao `Listar propostas auditaveis`
- uso de `POST /local/plan/proposals`
- uso de `GET /local/plan/proposals`
- smoke `scripts/helpusai/smoke_admin_local_audit_proposals_panel.py`
- script `npm run smoke:phase-c-ui`

Invariantes mantidas: proposal_only, executed=false, approved=false e approval_status=pending_human_review.

## Checkpoint: Phase C Executor Absence Guard

Added regression guard to ensure the local audit/proposal layer remains proposal-only and does not introduce command execution or approval endpoints.

Delivered scope:

- `scripts/38_smoke_local_executor_absent.py`
- `npm run smoke:phase-c-safety`
- `npm run smoke:phase-c` now includes audit, UI, safety, Phase B, admin, and build validations
- updated `docs/local-plan-audit.md`

Maintained invariants: no `/local/execute`, no `/local/plan/execute`, no `/local/plan/run`, no approval endpoint, no subprocess execution in the audit module, and proposal records remain `executed=false` and `approved=false`.

## Checkpoint: Phase D Audit Integrity

Added canonical hash integrity for local plan proposal records while keeping the system proposal-only.

Delivered scope:

- `record_hash` and `previous_record_hash` on new proposal records
- `integrity_version = local-plan-audit-integrity-v1`
- `integrity_algorithm = sha256-json-v1`
- read-only `GET /local/plan/proposals/verify`
- `scripts/39_smoke_local_audit_integrity.py`
- `npm run smoke:phase-d-integrity`
- `npm run smoke:phase-d` chains integrity, Phase C, Phase B, admin, and build validation

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and proposal records remain `executed=false` and `approved=false`.

## Checkpoint: Phase E Audit Integrity UI

Added admin UI visibility for the read-only local plan proposal integrity verifier.

Delivered scope:

- `Verificar integridade auditavel` button in `/admin/local`
- `Resultado da integridade` JSON panel
- read-only call to `GET /local/plan/proposals/verify`
- `scripts/helpusai/smoke_admin_local_audit_integrity_panel.py`
- `npm run smoke:phase-e-ui`
- `npm run smoke:phase-e` chains Phase E UI, Phase D, Phase C, Phase B, admin, and build validation

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and proposal records remain `executed=false` and `approved=false`.

2# Checkpoint: Phase F Verify API Contract

Added a dedicated regression smoke for the read-only verify API contract.

Delivered scope:

- `scripts/40_smoke_local_plan_verify_api_contract.py`
- `npm run smoke:phase-f-verify-api`
- `npm run smoke:phase-f` chains Phase F, E, D, C, B, admin, and build validation

The smoke confirms that the verify endpoint is GET-only, that it delegates to the audit integrity verifier, and that the verifier does not mutate the proposal store.

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and proposal records remain `executed=false` and `approved=false`.

## Checkpoint: Phase G Summary API Contract

Added a read-only proposal summary API contract.

Delivered scope:

- `summarize_local_plan_proposals(limit=200)`
- `GET /local/plan/proposals/summary`
- `scripts/41_smoke_local_plan_summary_api_contract.py`
- `npm run smoke:phase-g-summary-api`
- `npm run smoke:phase-g` chains Phase G, F, E, D, C, B, admin, and build validation

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and proposal records remain `executed=false` and `approved=false`.

## Checkpoint: Phase H Summary UI Contract

Added the read-only proposal summary UI to the admin local panel.

Delivered scope:

- proposalSummary admin state
- carregarResumoPropostas() read-only fetch helper
- Carregar resumo auditavel action button
- Resumo auditavel JSON display block
- scripts/helpusai/smoke_admin_local_audit_summary_panel.py
- npm run smoke:phase-h-ui
- npm run smoke:phase-h chains Phase H, G, F, E, D, C, B, admin, and build validation

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and proposal records remain executed=false and approved=false.


## Checkpoint: Phase I Detail API Contract

Added the read-only proposal detail API for retrieving one stored proposal by `proposal_id`.

Delivered scope:

- `get_local_plan_proposal(proposal_id)` in the audit module
- `GET /local/plan/proposals/{proposal_id}` in the backend
- `scripts/42_smoke_local_plan_detail_api_contract.py`
- `npm run smoke:phase-i-detail-api`
- `npm run smoke:phase-i` chaining Phase I through Phase H

Maintained invariants: no local execution endpoint, no approval endpoint, no subprocess execution in the audit module, and detail lookups do not mutate the proposal store.

## Checkpoint Phase J Detail UI read-only

Status: implementado.

- UI `/admin/local` ganhou campo `proposal_id para detalhe auditavel`.
- Botao `Carregar detalhe auditavel` consulta `GET /local/plan/proposals/{proposal_id}`.
- Resultado exibido no bloco `Detalhe da proposta`.
- Contrato mantido: read-only/proposal-only, sem approval, sem executor.
- Validacao planejada: `npm run smoke:phase-j`.

## Checkpoint Phase K Detail quick-fill UI read-only

Status: implemented.

- UI `/admin/local` gained helper `findProposalId` to extract `proposal_id` from created/listed proposal responses.
- Actions `Preencher id da proposta criada` and `Preencher id da lista` only fill the detail input.
- Detail lookup remains separate in `Carregar detalhe auditavel`, via read-only GET.
- Contract preserved: no executor, no approval, no execution endpoint.

## Checkpoint Phase L Detected proposal_id hint UI read-only

Status: implemented. The admin local panel shows the detected proposal id from local UI state only, preserving read-only/proposal-only behavior.

## Checkpoint Phase M Endpoint preview UI read-only

Status: implemented.

- UI `/admin/local` now shows `Preview GET detalhe auditavel`.
- The preview is computed from the manual/detail input state only.
- It does not call any API, mutate audit records, approve anything, or execute commands.

## Checkpoint Phase N Detail proposal_id status UI read-only

Status: implemented.

- UI `/admin/local` now shows `Status do proposal_id para detalhe`.
- The status is computed from the manual/detail input state only.
- It does not call any API, mutate audit records, approve anything, or execute commands.

## Checkpoint Phase O Detail normalized proposal_id UI read-only

Status: implemented.

- UI `/admin/local` now shows `proposal_id normalizado para detalhe`.
- The normalized value is computed from the manual/detail input state only.
- It does not call any API, mutate audit records, approve anything, or execute commands.

## Checkpoint Phase P Detail encoded proposal_id UI read-only

Status: implemented.

- UI `/admin/local` now shows `proposal_id codificado para endpoint de detalhe`.
- The encoded value is computed from the manual/detail input state only.
- It does not call any API, mutate audit records, approve anything, or execute commands.

## Checkpoint Phase Q Detail GET checklist UI read-only

Status: implemented.

- UI `/admin/local` now shows `Checklist GET detalhe auditavel`.
- The checklist is static/read-only and does not call any API, fill fields, approve anything, mutate audit records, or execute commands.
- It documents the safe user flow before clicking `Carregar detalhe auditavel`.

## Checkpoint Phase R Detail GET boundary UI read-only

Status: implemented.

- UI `/admin/local` now shows `Limite da consulta GET de detalhe`.
- The boundary is static/read-only and does not call any API, fill fields, approve anything, mutate audit records, or execute commands.
- It documents that the detail GET lookup happens only via `Carregar detalhe auditavel`.

## Checkpoint Phase R Detail result guide UI read-only

Status: implemented.

- UI `/admin/local` now shows `Guia do resultado do detalhe`.
- The guide explains `found`, `proposal`, and the expectation that `executed` and `approved` remain false.
- It is static/read-only and does not call any API, fill fields, approve anything, mutate audit records, or execute commands.

## Checkpoint Phase R Detail GET contract UI read-only

Status: implemented.

- UI `/admin/local` now shows `Contrato GET detalhe auditavel`.
- The contract is static/read-only and documents the safe GET detail lookup behavior.
- It does not call any API, fill fields, approve anything, mutate audit records, or execute commands.

## Checkpoint Phase S Detail safety aggregate smoke

Status: implemented.

- Added `scripts/43_smoke_local_detail_ui_safety_contract.py`.
- Added `smoke:phase-s-detail-safety` and `smoke:phase-s`.
- The aggregate safety smoke validates the detail read-only guidance area and guards against unsafe executor/approval patterns.

## Checkpoint Phase T Detail safety smoke alias

Status: implemented.

- Added `smoke:local-detail-safety`.
- Added `smoke:phase-t-alias` and `smoke:phase-t`.
- Added `scripts/44_smoke_local_detail_safety_alias.py`.
- The alias combines the aggregate detail safety contract with the executor absence guard.

## Checkpoint Phase U Local audit safety index

Status: implemented.

- Added `smoke:local-audit-safety`.
- Added `smoke:phase-u-index` and `smoke:phase-u`.
- Added `scripts/45_smoke_local_audit_safety_index.py`.
- The index validates Phase T aliases, detail read-only safety markers, docs markers, and executor absence guard coverage.

## Checkpoint docs AI capabilities and next steps

Status: implemented.

Added `docs/ai/CAPABILITIES_AND_NEXT_STEPS.md` with:

- current AI capabilities;
- current Phase U safety baseline;
- validated smoke markers;
- validated npm aliases;
- recommended next phases V through Z.

Current baseline remains `076c495 test: add local audit safety index`.

Primary safety command: `npm run smoke:local-audit-safety`.

## Checkpoint Phase V AI capabilities panel

Status: implemented.

Added a read-only AI capabilities panel to `/admin/local`.

Validation:

- `python scripts/46_smoke_ai_capabilities_panel.py`
- `npm run smoke:phase-v`
- `npm run smoke:local-audit-safety`

Safety posture remains read-only, proposal-oriented, non-executing, and non-approving inside the application.

## Checkpoint Phase W structured proposal risk scoring

Status: implemented.

Added a read-only structured risk panel to `/admin/local`.

Validation:

- `python scripts/47_smoke_structured_proposal_risk_panel.py`
- `npm run smoke:phase-w`
- `npm run smoke:phase-v`
- `npm run smoke:local-audit-safety`

Safety posture remains read-only, proposal-oriented, non-executing, and non-approving inside the application.

## Checkpoint Phase X CI safety workflow

Status: implemented.

Added GitHub Actions workflow `.github/workflows/local-audit-safety.yml`.

Validation:

- `python scripts/48_smoke_ci_safety_workflow.py`
- `npm run smoke:phase-x`
- `npm run smoke:phase-w`

Safety posture remains read-only, proposal-oriented, non-executing, and non-approving inside the application.

## Checkpoint Phase Y multi-agent handoff docs

Status: implemented.

Validation:

- `python scripts/49_smoke_multi_agent_handoff_docs.py`
- `npm run smoke:phase-y`
- `npm run smoke:phase-x`

## Checkpoint Phase Z patch proposal mode

Status: implemented.

Validation:

- `python scripts/50_smoke_patch_proposal_mode.py`
- `npm run smoke:phase-z`
- `npm run smoke:phase-y`

No application-level patch execution or automatic approval was added.

## Checkpoint Phase AA CI Phase Z chain

Status: implemented.

The local audit safety workflow now validates the complete Phase Z chain.

Validation:

- `python scripts/51_smoke_ci_phase_z_chain.py`
- `npm run smoke:phase-aa`
- `npm run smoke:phase-z`

Safety posture remains proposal-only and non-executing inside the application.

## Checkpoint Phase AB handoff summary preview

Status: implemented.

Validation:

- `python scripts/52_smoke_handoff_summary_preview.py`
- `npm run smoke:phase-ab`
- `npm run smoke:phase-aa`

The panel remains read-only and does not contact another agent automatically.

## Checkpoint Phase AC handoff copy support

Status: implemented.

Validation:

- `python scripts/53_smoke_handoff_copy_clipboard.py`
- `npm run smoke:phase-ac`
- `npm run smoke:phase-ab`

Copying requires an explicit click and remains local to the browser clipboard.

## Checkpoint Phase AD CI Phase AC chain

Status: implemented.

Validation:

- `python scripts/54_smoke_ci_phase_ac_chain.py`
- `npm run smoke:phase-ad`
- `npm run smoke:phase-ac`

CI now covers the complete handoff-copy safety chain.

## Checkpoint Phase AE handoff download

Status: implemented.

Validation:

- `python scripts/55_smoke_handoff_download.py`
- `npm run smoke:phase-ae`
- `npm run smoke:phase-ad`

The handoff download is local, explicit, non-transmitting, and non-executing.

## Checkpoint Phase AF CI Phase AE chain

Status: implemented.

Validation:

- `python scripts/56_smoke_ci_phase_ae_chain.py`
- `npm run smoke:phase-af`
- `npm run smoke:phase-ae`

CI now covers the complete local handoff-download safety chain.

## Checkpoint Phase AG handoff readiness

Status: implemented.

Validation:

- `python scripts/57_smoke_handoff_readiness_checklist.py`
- `npm run smoke:phase-ag`
- `npm run smoke:phase-af`

The checklist remains read-only, informational, non-approving, non-transmitting, and non-executing.

## Checkpoint Phase AH CI Phase AG chain

Status: implemented.

Validation:

- `python scripts/58_smoke_ci_phase_ag_chain.py`
- `npm run smoke:phase-ah`
- `npm run smoke:phase-ag`

CI now covers the complete read-only handoff-readiness chain.

## Checkpoint Phase AI handoff JSON export

Status: implemented.

Validation:

- `python scripts/59_smoke_handoff_json_export.py`
- `npm run smoke:phase-ai`
- `npm run smoke:phase-ah`

The export is read-only, local, non-transmitting, non-approving, and non-executing.

## Checkpoint Phase AJ CI Phase AI chain

Status: implemented.

Validation:

- `python scripts/60_smoke_ci_phase_ai_chain.py`
- `npm run smoke:phase-aj`
- `npm run smoke:phase-ai`

CI now covers the complete read-only handoff JSON-export chain.

## Checkpoint Phase AK handoff fingerprint

Status: implemented.

Validation:

- `python scripts/61_smoke_handoff_fingerprint.py`
- `npm run smoke:phase-ak`
- `npm run smoke:phase-aj`

The fingerprint is local, explicit, informational, non-approving, non-transmitting, and non-executing.

## Checkpoint Phase AL CI Phase AK chain

Status: implemented.

Validation:

- `python scripts/62_smoke_ci_phase_ak_chain.py`
- `npm run smoke:phase-al`
- `npm run smoke:phase-ak`

CI now covers the complete read-only handoff-fingerprint safety chain.

## Checkpoint Phase AM fingerprint comparison

Status: implemented.

Validation:

- `python scripts/63_smoke_handoff_fingerprint_comparison.py`
- `npm run smoke:phase-am`
- `npm run smoke:phase-al`

The comparison is explicit, local, informational, non-approving, non-authorizing, non-transmitting, and non-executing.

## Checkpoint Phase AN CI Phase AM chain

Status: implemented.

Validation:

- `python scripts/64_smoke_ci_phase_am_chain.py`
- `npm run smoke:phase-an`
- `npm run smoke:phase-am`

CI now covers the complete read-only fingerprint-comparison safety chain.

## Checkpoint Phase AO chat navigation

Status: implemented.

The main sidebar now uses the real authenticated conversation history and provides reopening, search, refresh, link copying, local aliases, deletion confirmation, active-chat highlighting, and responsive navigation.

Validation:

- `python scripts/65_smoke_chat_sidebar_navigation.py`
- `npm run smoke:phase-ao`
- `npm run smoke:phase-an`

## Checkpoint Phase AP CI Phase AO chain

Status: implemented.

CI now covers:

- the flat conversation list;
- conversation search;
- reopening existing chats;
- list refresh;
- local title aliases;
- link copying;
- deletion confirmation;
- active-conversation highlighting;
- responsive sidebar behavior;
- account and operational-panel controls.

Validation:

- `python scripts/66_smoke_ci_phase_ao_chain.py`
- `npm run smoke:phase-ap`
- `npm run smoke:phase-ao`
