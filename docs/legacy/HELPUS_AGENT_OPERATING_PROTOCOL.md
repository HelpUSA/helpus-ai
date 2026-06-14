# HelpUS Agent Operating Protocol

Este documento define o protocolo operacional que o chat HelpUS deve seguir para evoluir o repositorio `D:/dev/ai` com seguranca e autonomia supervisionada.

## Objetivo

Dar ao agente HelpUS um roteiro objetivo para entender o estado do projeto, propor proximas atividades, executar inspecoes, aplicar patches pequenos, validar resultados e parar quando houver risco.

## Escopo do agente

O agente opera o repositorio principal:

- Repo: `D:/dev/ai`
- Branch padrao: `main`
- Remoto: `origin/main`
- Tags seguras recentes:
  - `helpus-admin-telemetry-ui-docs-2026-06-13`
  - `helpus-admin-telemetry-ui-2026-06-13`
  - `helpus-operational-suite-admin-telemetry-2026-06-12`
  - `helpus-operational-suite-2026-06-12`

O agente nao deve tratar recibos `[AI_LOCAL]`, `[AI_LOCAL_RUN]` ou `[AI_LOCAL_ERRO]` como comandos de entrada. Esses blocos sao resultados do watcher e devem ser analisados antes de propor o proximo passo.

## Fontes de contexto obrigatorias

Antes de propor alteracoes, consultar quando relevante:

- `docs/HELPUS_OPERATIONAL_AUTOMATION.md`
- `docs/HELPUS_AI_BRIDGE_OPERATIONS_2026-06-12.md`
- `docs/HELPUS_AI_HISTORY_AND_PROJECT_MEMORY_BACKLOG_2026-06-12.md`
- `docs/HELPUS_AI_OPERATIONS.md`

## Rotina segura antes de qualquer alteracao

1. Confirmar o repo e branch com `git status -sb`.
2. Confirmar o HEAD com `git rev-parse --short HEAD`.
3. Identificar a tag segura mais recente quando a tarefa envolver baseline ou rollback.
4. Fazer uma inspecao somente leitura antes de qualquer patch.
5. Propor uma tarefa pequena, incremental e validavel.
6. Alterar o menor numero possivel de arquivos.
7. Rodar a suite real do repo.
8. Mostrar `git diff --stat` e revisar se apenas arquivos esperados mudaram.
9. Commitar apenas apos validacao verde.
10. Nunca fazer deploy automatico sem autorizacao explicita.

## Validacoes reais obrigatorias

Antes de commit ou tag, executar:

```powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check
```

Quando a tarefa alterar um contrato especifico, executar tambem o smoke especifico relacionado, por exemplo:

```powershell
python scripts/watcher/smoke_admin_telemetry.py
python scripts/watcher/smoke_admin_telemetry_route_contract.py
python scripts/watcher/smoke_admin_telemetry_ui_contract.py
```

## Comandos destrutivos ou sensiveis

Exigem dry-run, explicacao do impacto e autorizacao explicita:

- `git reset --hard`
- `git clean -fd` ou `git clean -fdx`
- `git push --force`
- remocoes em massa (`rm -rf`, `Remove-Item -Recurse`, `del /s`)
- migracoes ou alteracoes destrutivas de banco
- deploy
- alteracao de secrets, variaveis de producao ou credenciais

## Como escolher a proxima atividade

Priorizar nesta ordem:

1. Inspecao do estado atual.
2. Documentacao/protocolo quando faltar clareza operacional.
3. Smokes/contratos antes de UI ou funcionalidade nova.
4. Backend pequeno e testavel.
5. Frontend pequeno e testavel.
6. Tag apenas quando a suite estiver verde e o repo limpo.

## Criterio de pronto

Uma tarefa esta pronta quando:

- objetivo e escopo foram cumpridos;
- validacoes reais passaram;
- `git diff --check` passou;
- diff contem apenas arquivos esperados;
- commit foi feito com mensagem objetiva;
- push para `origin/main` foi concluido;
- repo ficou limpo/alinhado.

## Quando parar

Parar e reportar ao usuario quando:

- houver erro de parse de envelope watcher;
- houver erro de build, smoke ou diff check;
- aparecer arquivo modificado inesperado;
- o comando proposto exigir autorizacao;
- a tarefa exigir deploy;
- o agente nao conseguir identificar o arquivo correto com seguranca.

## Proximas frentes atuais

Depois desta baseline operacional, as proximas frentes recomendadas sao:

1. Melhorar telemetria admin com `latest_event_at`, `latest_error_at`, `latest_failed_event_type` e `recent_events`.
2. Fazer inspecao visual/manual do painel `/admin`.
3. Criar documentacao curta de uso do painel admin.
4. Adicionar testes de rota com FastAPI/TestClient quando a autenticacao puder ser mockada com seguranca.

## Referencia para IA local/offline

Para evoluir a autonomia do chat com privacidade, consultar tambem:

- docs/HELPUS_LOCAL_AI_PROVIDER.md

O provedor local e opcional e deve ser usado apenas como apoio analitico. Execucao, patch, commit, tag e deploy continuam passando pelo watcher e pelas validacoes reais.
