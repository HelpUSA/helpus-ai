# HelpUS AI - Documento Mestre Unificado

Este documento e a fonte principal do projeto HelpUS AI. Ele consolida toda a documentacao em um unico arquivo e preserva documentos historicos em docs/legacy.

## 1. Estado atual consolidado

- Repo principal: D:/dev/ai
- Branch principal: main
- Remoto principal: origin/main
- Estado final conhecido: HEAD f8b29c2 em main origin/main, repo limpo e alinhado.
- Micros 24 a 29 concluidos.
- Relatorio final versionado: reports/HELPUS_FINAL_REPORT_2026-06-14.md.
- Validacoes finais conhecidas: py_compile, smoke_operational_release, smoke_health_report, npm build e git diff --check.
- Sem deploy, sem tag, sem reset hard e sem git clean.

## 2. Principio operacional atual

O watcher / AI Bridge Local continua sendo o caminho operacional atual para execucao, validacao, commit e push. Ele deve ser usado com comandos pequenos, cwd explicito, command_id novo, validacoes reais e resumo do resultado. Recibos AI_LOCAL, AI_LOCAL_RUN e AI_LOCAL_ERRO devem ser tratados como resultados, nao como novos pedidos.

## 3. O que ja foi feito

- Documentacao operacional consolidada em docs/HELPUS_PROJECT_MASTER.md.
- Documentos antigos movidos para docs/legacy.
- Micro 24: operational_context para carregar contexto operacional local.
- Micro 25: watcher_intent para classificar pedidos, recibos e acoes sensiveis.
- Micro 26: smoke/estrutura para envelope builder usando CommandBuilder.
- Micro 27: watcher_recovery para interpretar falhas e orientar recuperacao.
- Micro 28: orquestracao do chat watcher conectando contexto, intencao, builder e recovery.
- Micro 29: provedor local/offline de IA opcional.
- Relatorio final criado em reports/HELPUS_FINAL_REPORT_2026-06-14.md.

## 4. Nova direcao arquitetural

A evolucao natural do HelpUS AI e reduzir a dependencia da extensao e do watcher para tarefas internas, criando uma API propria com backend, banco, workers, executor interno e mensageria entre agentes. A extensao pode continuar como ponte temporaria ou fallback, mas o objetivo futuro e que o proprio HelpUS AI controle leitura, execucao, logs, comandos e conversas entre agentes.

## 5. API propria para arquivos

Criar uma API local para acesso a arquivos e repositorios. A primeira fase deve ser principalmente read-only para acelerar diagnostico sem depender de envelopes. Endpoints sugeridos: listar arquivos permitidos, ler arquivo, buscar em docs, ver git status, ver diff, ver HEAD, ler relatorios e consultar logs.

## 6. API propria para comandos

E possivel criar uma API para executar comandos sem watcher. Como o ambiente e de uso individual e possui backups, a primeira versao pode ser menos restritiva para ganhar velocidade. Mesmo assim, manter freios minimos que nao atrapalham: log de tudo, cwd explicito, timeout, stdout, stderr, return_code, historico auditavel e confirmacao antes de comandos destrutivos evidentes. Blacklist e politicas mais fortes podem vir depois.

## 7. Executor interno futuro

O executor interno deve substituir gradualmente o watcher. Fluxo sugerido: agente cria command_request, backend salva no banco, worker local executa, command_result volta estruturado, agente interpreta e decide o proximo passo. Campos minimos: command_id, cwd, command, status, return_code, stdout, stderr, started_at, finished_at, files_changed e summary.

## 8. Conversas entre agentes sem extensao

A comunicacao entre chats/agentes pode ser feita sem extensao se os agentes estiverem dentro do HelpUS AI ou conectados ao backend. Modelo sugerido: tabela messages com id, source_agent_id, target_agent_id, conversation_id, kind, message, status, created_at, read_at e ack_at. O chat A grava mensagem no backend e o chat B recebe por polling, SSE ou WebSocket.

## 9. UI multiagente futura

Criar uma tela propria para supervisor, executor, auditor, planner e agente de docs. A UI deve mostrar mensagens, filas de comandos, resultados, logs, diffs e relatorios. Isso substitui o uso de varias abas de ChatGPT e reduz erro humano de copiar envelopes.

## 10. Seguranca progressiva sem travar velocidade

Comecar simples: uso individual, logs completos, backups e blacklist minima. Depois evoluir para allowlist, confirmacao humana, perfis, RBAC, protecao de secrets, auditoria e politicas por ambiente. Nao precisa travar a fase inicial com seguranca pesada, mas tambem nao deve executar silenciosamente acoes perigosas sem rastro.

## 11. Roadmap atualizado

### Fase A - API local de leitura
- Endpoints para status, diff, logs, docs e leitura de arquivos.
- Busca em docs/HELPUS_PROJECT_MASTER.md e reports.
- Sem execucao livre nesta fase, exceto comandos de diagnostico predefinidos se necessario.

### Fase B - Mensageria entre agentes
- Criar tabela messages.
- Criar agent_id, conversation_id e status.
- Implementar envio, leitura, ack e historico.
- Permitir que agentes se comuniquem sem extensao.

### Fase C - Executor interno
- Criar command_requests e command_results.
- Criar worker local.
- Capturar stdout, stderr, return_code, timeout e arquivos alterados.
- Substituir gradualmente run-command do watcher.

### Fase D - Orquestrador operacional
- Agente decide entre inspecionar, patchar, validar, commitar, pushar ou pedir autorizacao.
- Integrar contexto operacional, recovery e executor interno.
- Gerar relatorios de cada micro automaticamente.

### Fase E - UI multiagente
- Painel para supervisor, executor, auditor e planner.
- Visualizacao de mensagens, fila de comandos, logs, diffs e validacoes.
- Botoes para aprovar comandos sensiveis quando necessario.

### Fase F - Seguranca incremental
- Blacklist inicial para comandos perigosos.
- Confirmacao para deploy, tag, reset hard, git clean, secrets e remocoes em massa.
- Depois adicionar roles, politicas por ambiente e auditoria avancada.

## 12. Regras atuais enquanto o watcher ainda existir

- Use watcher para executar no repo.
- Use send-chat-message apenas para reportar ou coordenar entre chats.
- Nunca tratar recibo AI_LOCAL como pedido novo.
- Em envelope_parse_error, considerar que nada executou, gerar command_id novo e simplificar.
- Em falha parcial, inspecionar antes de corrigir.
- Validar antes de commit: py_compile, smoke especifico, smoke_operational_release, smoke_health_report, npm build e git diff --check.
- Nao fazer deploy/tag sem decisao humana explicita.

## 13. Validacoes recomendadas

git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check

## 14. Fontes documentais consolidadas

## Fechamento final 2026-06-14

Status final: Micros 24 a 29 concluidos, validados, commitados e enviados para origin/main. Local AI permanece analysis_only. Sem deploy, tag, reset hard, git clean, secrets ou remocoes em massa sem autorizacao.

## Active documentation index

Active documentation is indexed in docs/README.md. The active set is the master document, release and deploy checklist, watcher operations runbook, post completion backlog and final report.

Nota operacional: estado pos-conclusao segue sem deploy, sem tag e com IA local em analysis_only ate autorizacao explicita.

Nota operacional: estado pos-conclusao segue sem deploy, sem tag e com IA local em analysis_only ate autorizacao explicita.

Release, tag and deploy gates permanecem documentados em legacy; Post completion backlog e Active documentation index permanecem como referencia historica; estado atual segue sem deploy e analysis_only ate autorizacao explicita.

## Micro documentacao watcher segura

Objetivo: reduzir envelope_parse_error e falhas por comandos inline frageis ao operar HelpUS AI via watcher / AI Bridge Local.

### Modelos seguros
- send-chat-message: manter message no topo do JSON, usar command_id novo e unico, evitar mensagens muito longas com quebras nao escapadas.
- run-command readonly: preferir comandos curtos para git status -sb, git log, git diff --stat, git diff --check e leitura limitada de arquivos.
- run-command de patch: inspecionar antes, alterar apenas arquivos esperados, validar, commitar e pushar somente apos suite OK.
- pos-falha: se AI_LOCAL_ERRO envelope_parse_error, assumir que nada executou, criar command_id novo e simplificar.
- pos-falha: se AI_LOCAL_RUN return_code diferente de zero, assumir execucao parcial possivel, inspecionar status e diff antes de corrigir.

### Erros recorrentes a evitar
- Nao usar $.FullName; usar $PSItem.FullName em PowerShell quando necessario.
- Nao usar Write-Output $ solto; imprimir variaveis explicitamente.
- Nao repetir command_id apos erro de parse.
- Nao enviar mensagem longa com quebras nao escapadas dentro de JSON inline.
- Nao misturar leitura, patch amplo, deploy, tag e limpeza no mesmo micro.
- Nao usar reset hard, git clean, secrets, deploy ou tag sem autorizacao explicita.

### Sequencia padrao
1. Inspecionar: git status -sb, git log --oneline --decorate -8, git diff --stat e git diff --check.
2. Planejar micro pequeno e listar arquivos esperados.
3. Patch minimo apenas nos arquivos esperados.
4. Validar smoke especifico, smoke_operational_release, smoke_health_report, npm build quando aplicavel e git diff --check.
5. Conferir diff, git add somente arquivos esperados, commit pequeno e push.

## Release readiness sem deploy 2026-06-14

Validacao executada sem deploy e sem tag. Repo iniciou limpo e alinhado com origin/main. Foram revisados o log recente, o relatorio final e marcadores do documento mestre. Validacoes executadas: smoke_operational_release, smoke_health_report, npm build e git diff --check.

Recomendacao: o projeto esta apto para uma decisao humana separada sobre tag/release formal, desde que a validacao completa seja repetida imediatamente antes da tag. Nenhuma tag ou release deve ser criada sem autorizacao explicita. Nenhum deploy foi executado.

## Preparacao de deploy sem executar deploy 2026-06-14

Objetivo: preparar um runbook de deploy e rollback sem executar deploy, sem criar tag, sem alterar secrets e sem fazer comandos destrutivos.

### Pre-condicoes obrigatorias
- Repo limpo e alinhado com origin/main.
- Release readiness repetido imediatamente antes de qualquer tag ou deploy.
- Autorizacao humana explicita para deploy, em comando separado.
- Health checks definidos antes da janela de deploy.
- Variaveis de ambiente confirmadas apenas por nome, sem imprimir valores.

### Health checks obrigatorios
- Aplicacao inicia sem erro.
- Endpoint de health responde OK quando disponivel.
- smoke_health_report passa.
- smoke_operational_release passa.
- npm --prefix frontend run build passa.
- git diff --check passa.

### Variaveis esperadas sem imprimir secrets
- Confirmar nomes e presenca das variaveis necessarias no ambiente alvo.
- Nunca imprimir valores de secrets em stdout, logs, docs ou mensagens watcher.
- Se variavel obrigatoria faltar, abortar antes do deploy.

### Plano de rollback
- Registrar commit/tag implantado antes do deploy.
- Confirmar comando de rollback antes de iniciar.
- Se health check falhar, voltar para a versao anterior conhecida como boa.
- Registrar stdout, stderr e return_code do rollback.

### Criterios de abortar
- Repo sujo.
- Build, smoke ou diff-check falhando.
- Secrets ausentes ou expostos.
- Plano de rollback indefinido.
- Autorizacao humana ausente.

### Criterios de sucesso
- Deploy autorizado separadamente.
- Health checks OK apos deploy.
- Logs sem erros criticos.
- Rollback nao necessario ou testado/documentado.

Nenhum deploy foi executado por este micro. Nenhuma tag foi criada. Nenhum secret foi impresso.
