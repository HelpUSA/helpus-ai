---
type: roadmap
project: HelpUSAI
area: ai-helpus
status: active
updated: 2026-07-04
tags:
 - helpusai
 - roadmap
 - obsidian
---

# HelpUSAI - Roadmap operacional Obsidian

## Principio

A aplicacao deve evoluir com pequenas alteracoes verificaveis. A documentacao em Obsidian deve explicar estado atual, decisao tomada e proximo passo.

## Agora

- Manter HelpUSAI limpo e validado.
- Usar o painel admin de operational lessons como ponto de auditoria.
- Manter exportacao e notas Obsidian apenas onde reduzem retrabalho.
- Nao integrar providers experimentais que possam virar dependencia instavel.

## Proximo ciclo

1. Revisar a experiencia do painel admin de operational lessons.
2. Conferir se as licoes exibidas sao as mesmas usadas no contexto operacional.
3. Adicionar smoke para qualquer nova rota ou transformacao de dados.
4. Atualizar esta nota ao final de cada ciclo.

## Backlog seguro

- Melhorar indice Obsidian.
- Criar checklist de release HelpUSAI.
- Criar relatorio de gaps de docs.
- Revisar dead letters somente em dry-run.

## Fora de escopo por enquanto

- Integrar NVIDIA NIM ou outro provider gratuito como dependencia da aplicacao.
- Fazer mudancas grandes em backend e frontend no mesmo commit sem smoke especifico.
- Usar dados sensiveis em endpoints experimentais.

## Links internos

- [[README|Indice Obsidian HelpUSAI]]
- [[HELPUSAI_STATUS_2026-07-04|Estado atual e direcao]]

## Checkpoint 2026-07-06 - Fase A Local Readonly API

Status: concluido e validado.

A API local read-only agora possui os blocos essenciais para diagnostico seguro do repositorio sem depender exclusivamente do watcher:

- `/local/status` para status Git resumido.
- `/local/diff` para diff/check read-only.
- `/local/files/read` para leitura segura de arquivo allowlisted.
- `/local/files/list` para listagem segura de arquivos allowlisted.
- `/local/docs/search` para busca segura em documentos locais.

Validacoes do checkpoint:

- Smoke local da API read-only passando.
- Build frontend passando.
- `git diff --check` limpo.
- Commit publicado: `ddd57bd feat: add local readonly file list and search`.

Proxima direcao: usar esses endpoints como base para uma UI/operador local de diagnostico, mantendo todas as acoes destrutivas fora da Fase A.

## Checkpoint 2026-07-06 - UI Admin Local Readonly

Status: concluido e validado.

Foi adicionada uma UI isolada em `/admin/local` para consumir os endpoints locais read-only da Fase A. A rota foi ligada ao painel `/admin` e recebeu smoke oficial via `npm run smoke:admin-local`.

Escopo entregue:

- Painel read-only para status Git local.
- Painel read-only para diff local.
- Listagem segura de `docs/`.
- Busca segura em `docs/`.
- Link de navegacao no admin principal.
- Smokes dedicados para painel e link.

Commits do checkpoint:

- `adf140f feat: add admin local readonly panel`
- `7538598 feat: link admin to local readonly panel`
- `97a75a1 test: add admin local readonly smoke script`

Proxima direcao: evoluir do diagnostico read-only para um operador de planejamento seguro, mantendo execucao real separada por gates explicitos.

## Checkpoint 2026-07-06 - Validacao Consolidada da Fase A

Status: concluido e validado.

Foi criado o comando `npm run smoke:phase-a` para validar a Fase A inteira em uma unica execucao.

Composicao do comando:

- `npm run smoke:local-api`
- `npm run smoke:admin-local`
- `npm run build`

Commit do checkpoint:

- `c2e1018 test: add phase A validation script`

A partir daqui, a Fase A pode ser tratada como base operacional read-only concluida. A proxima frente recomendada e a Fase B: operador de planejamento seguro, ainda sem execucao automatica.

## Checkpoint 2026-07-06 - Fase B Plan-only API

Status: iniciado e validado.

Foi criada a primeira camada da Fase B: `POST /local/plan`, um endpoint que gera decisoes de planejamento seguro sem executar comandos.

Escopo entregue:

- Planejamento por intent conhecido, como `phase_a_validation`, `local_status`, `local_diff`, `local_api_smoke`, `admin_local_smoke` e `build`.
- Classificacao de comandos allowlisted read-only.
- Bloqueio explicito de tokens destrutivos como `git push`, `git commit`, `git reset`, `git clean`, remocoes, deploys e downloads remotos.
- Smoke oficial: `npm run smoke:phase-b-plan`.

Proxima direcao: expor este planner na UI `/admin/local`, ainda sem botao de execucao.

## Checkpoint 2026-07-06 - Fase B Plan-only UI

Status: concluido e validado.

A UI `/admin/local` agora consome `POST /local/plan` e exibe planos seguros sem execucao.

Escopo entregue:

- Card de planejamento seguro no operador local.
- Exibicao de plano read-only permitido para `phase_a_validation`.
- Exibicao de plano bloqueado para `git push origin main`.
- Smoke dedicado `npm run smoke:phase-b-ui`.
- Smoke consolidado `npm run smoke:phase-b`.

Proxima direcao: permitir entrada controlada de intent/comando na UI para planejamento customizado, mantendo execucao desabilitada.

## Checkpoint: Fase B Custom Planner Contract

Contrato `local-plan-v1` adicionado com `GET /local/plan/intents`, limites de comando, bloqueio de chaining, intent `phase_b_validation`, intent `local_recent_commits` e documento `docs/local-plan-contract.md`. A execuÃ§Ã£o segue desabilitada.

## Checkpoint: Fase C Audit Proposal Queue

Criada camada de auditoria proposal-only antes de qualquer execuÃ§Ã£o real.

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

## Phase J Detail UI read-only

Objetivo: permitir que o painel admin visualize o detalhe de uma proposta auditavel por `proposal_id`.

Entregaveis:

- Estado de UI para `proposalDetailId` e `proposalDetail`.
- Acao `carregarDetalheProposta` usando GET read-only.
- Marcadores de UI e smoke `smoke_admin_local_audit_detail_panel`.
- Script agregado `smoke:phase-j = npm run smoke:phase-j-ui && npm run smoke:phase-i`.

## Phase K Detail quick-fill UI read-only

Goal: reduce friction when viewing auditable proposal details in the admin panel.

Deliverables:

- UI helper `findProposalId`.
- Action `usarPropostaIdAuditavel` that only fills the detail field.
- Buttons `Preencher id da proposta criada` and `Preencher id da lista`.
- Smoke `smoke_admin_local_audit_detail_quickfill_panel`.
- Script `smoke:phase-k = npm run smoke:phase-k-ui && npm run smoke:phase-j`.
