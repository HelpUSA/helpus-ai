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

Contrato `local-plan-v1` adicionado com `GET /local/plan/intents`, limites de comando, bloqueio de chaining, intent `phase_b_validation`, intent `local_recent_commits` e documento `docs/local-plan-contract.md`. A execução segue desabilitada.

## Checkpoint: Fase C Audit Proposal Queue

Criada camada de auditoria proposal-only antes de qualquer execução real.

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
