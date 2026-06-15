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

## Plano API local de arquivos read-only 2026-06-14

Objetivo: planejar endpoints locais apenas de leitura para reduzir dependencia de comandos shell em tarefas de inspeção, mantendo o watcher como executor oficial.

### Escopo inicial read-only
- GET /local/status: retornar branch, HEAD curto, alinhamento com origin/main e dirty files, sem alterar nada.
- GET /local/diff: retornar git diff --stat e opcionalmente git diff --check, sem expor secrets.
- GET /local/files/read: ler arquivos permitidos com limite de tamanho e allowlist de diretorios.
- GET /local/docs/search: buscar termos em docs e reports com limite de linhas.
- GET /local/reports/latest: listar relatorios recentes e permitir leitura limitada.
- GET /local/logs/read: ler logs permitidos com redacao basica e limite de bytes.

### Regras de seguranca
- Sem execucao livre nesta fase.
- cwd fixo ou explicitamente validado.
- Allowlist de caminhos: docs, reports, scripts/watcher e arquivos de codigo especificos quando necessario.
- Bloquear leitura de .env, secrets, chaves, tokens, credenciais e arquivos binarios grandes.
- Sempre registrar request_id, path solicitado, status e tamanho retornado.

### Validacoes futuras
- Smoke para path traversal.
- Smoke para bloqueio de secrets.
- Smoke para limite de tamanho.
- Smoke para leitura de docs e reports.
- Smoke para status e diff read-only.

Decisao atual: apenas planejamento documentado. Nenhum endpoint foi implementado neste micro.

## Plano API local de comandos 2026-06-14

Objetivo: planejar um executor interno estruturado para comandos locais no futuro, sem substituir ainda o watcher e sem liberar execucao ampla nesta etapa.

### Modelo command_requests
- command_id unico e descritivo.
- source_agent_id e conversation_id.
- cwd explicito.
- command como lista, nunca string shell gigante por padrao.
- timeout_seconds obrigatorio.
- status inicial pending.
- created_at e requested_by.
- risk_level calculado antes de executar.

### Modelo command_results
- command_id vinculado ao request.
- started_at e finished_at.
- return_code.
- stdout e stderr com limite de tamanho.
- truncated_stdout e truncated_stderr quando aplicavel.
- status: succeeded, failed, timed_out, rejected ou aborted.
- logs auditaveis.

### Regras iniciais
- Watcher permanece executor oficial ate haver smokes e UI suficientes.
- Nenhum comando destrutivo sem autorizacao explicita.
- Bloquear ou exigir confirmacao para deploy, tag, reset hard, git clean, remocao em massa e secrets.
- Sempre inspecionar status e diff antes de corrigir falhas.
- Toda execucao deve produzir recibo estruturado equivalente a AI_LOCAL_RUN.

### Smokes futuros
- command_id unico.
- cwd obrigatorio.
- timeout obrigatorio.
- stdout/stderr capturados.
- return_code preservado.
- comandos perigosos rejeitados ou exigindo confirmacao.
- falha parcial orienta inspecao antes de patch.

Decisao atual: planejamento apenas. Nenhum endpoint ou executor novo foi implementado neste micro.

## Plano mensageria entre agentes sem extensao 2026-06-14

Objetivo: planejar uma mensageria backend-first para agentes HelpUSAI conversarem sem depender da extensao/browser como canal principal.

### Tabela messages proposta
- id: identificador unico.
- source_agent_id: agente remetente.
- target_agent_id: agente destino.
- conversation_id: agrupamento da conversa.
- kind: chat, command_request, command_result, audit_note, planning_note ou status.
- message: texto curto e estruturado.
- payload_json: dados estruturados opcionais.
- status: pending, sent, read, acked, failed ou archived.
- created_at, read_at e ack_at.
- correlation_id para relacionar pedido e resposta.

### Fluxo inicial
1. Supervisor cria mensagem para planner, executor, auditor ou docs agent.
2. Backend persiste a mensagem.
3. Agente destino lista pendentes e marca read_at.
4. Agente responde com status e ack_at.
5. UI exibe trilha completa por conversation_id.

### Regras de seguranca
- Mensagens nao executam comandos por si so.
- command_request deve passar por preflight e executor separado.
- Recibos seguem padrao AI_LOCAL_RUN / AI_LOCAL_ERRO ou equivalente interno.
- Secrets nao devem ser gravados em message nem payload_json.
- Toda mensagem deve ter source_agent_id, target_agent_id e conversation_id.

### Smokes futuros
- Criar mensagem pendente.
- Marcar como lida.
- Registrar ack.
- Correlacionar request/result.
- Bloquear mensagem sem agente destino.
- Bloquear payload com marcador de secret.

Decisao atual: planejamento apenas. Nenhuma tabela, migration ou endpoint foi implementado neste micro.

## Plano UI multiagente 2026-06-14

Objetivo: planejar um painel multiagente para coordenar supervisor, executor, auditor, planner e docs agent, sem implementar UI neste micro.

### Paineis propostos
- Supervisor: visao geral de conversas, objetivos, estado do repo e proximas decisoes.
- Planner: backlog, micro atual, arquivos esperados e plano de validacao.
- Executor: fila de comandos, status, stdout, stderr, return_code e tempo de execucao.
- Auditor: diffs, riscos, comandos bloqueados, secrets e regras permanentes.
- Docs agent: busca em docs, leitura de relatorios, sumarios e referencias.

### Componentes principais
- Timeline por conversation_id.
- Fila de command_requests e command_results.
- Visualizacao de git status, diff stat e diff check.
- Cards de smoke/build/health report.
- Indicadores de risco: deploy, tag, reset, git clean, secrets e remocao em massa.
- Botao de copiar envelope seguro.

### Estados visuais
- pending, running, succeeded, failed, rejected, timed_out e needs_human_authorization.
- Destaque para retorno diferente de zero.
- Destaque para repo sujo.
- Aviso quando o watcher ainda for executor oficial.

### Regras UX
- Mostrar sempre cwd, timeout e command_id.
- Nunca mostrar valores de secrets.
- Separar leitura, patch, validacao, commit e push.
- Nunca misturar deploy/tag com feature patch.
- Exigir confirmacao humana para acoes destrutivas.

### Smokes futuros
- Renderizar lista de agentes.
- Renderizar fila vazia.
- Renderizar command_result com stdout/stderr truncado.
- Renderizar alerta de repo sujo.
- Renderizar bloqueio de comando perigoso.
- Garantir que secrets sejam mascarados.

Decisao atual: planejamento apenas. Nenhuma UI foi implementada neste micro.

## Plano produto e UX 2026-06-14

Objetivo: organizar proximas melhorias de produto e UX sem alterar frontend neste micro.

### Telemetria admin
- Revisar clareza dos eventos exibidos.
- Separar eventos de usuario, sistema, watcher e IA local.
- Destacar falhas por return_code diferente de zero.
- Mostrar command_id, conversation_id e timestamp de forma copiavel.
- Evitar exibir secrets ou payloads sensiveis.

### Health report
- Melhorar localizacao e linguagem dos status.
- Exibir resumo curto: OK, alerta, falha e proxima acao.
- Incluir ultima validacao conhecida e commit associado.
- Mostrar quando o repo esta limpo/alinhado.
- Manter caminho para relatorio detalhado em reports.

### Toggle IA local analysis_only
- Deixar claro que IA local nao executa comandos.
- Exibir estado: disabled, analysis_only ou unavailable.
- Explicar que execucao continua via watcher/executor autorizado.
- Alertar quando usuario tentar pedir execucao pela IA local.

### Onboarding
- Criar passos iniciais: status do repo, ler docs mestre, escolher micro pequeno, validar, commit e push.
- Mostrar exemplos seguros de envelopes.
- Explicar diferenca entre AI_LOCAL_RUN, AI_LOCAL_ERRO e pedido novo.
- Reforcar proibicoes: deploy, tag, reset hard, git clean, secrets e remocao em massa sem autorizacao.

### Clareza de status
- Sempre mostrar micro atual, arquivos esperados, validacoes obrigatorias e resultado final.
- Usar estados consistentes: planejado, em execucao, validado, commitado, enviado e bloqueado.
- Em falha, sugerir primeira acao segura: inspecionar status/diff antes de corrigir.

Decisao atual: planejamento apenas. Nenhuma UI, rota ou componente foi alterado neste micro.

## Plano seguranca progressiva 2026-06-14

Objetivo: manter velocidade de desenvolvimento individual com controles progressivos que reduzem risco sem travar os micros seguros.

### Controles permanentes imediatos
- Logs de todos os comandos e resultados.
- cwd explicito em toda execucao.
- timeout obrigatorio.
- stdout, stderr e return_code preservados.
- command_id unico por tentativa.
- Inspecao de git status e git diff antes de corrigir falhas.
- Confirmacao humana para deploy, tag, reset hard, git clean, secrets e remocao em massa.

### Protecao de secrets
- Nunca imprimir valores de variaveis sensiveis.
- Bloquear leitura de .env e arquivos de credenciais em APIs read-only.
- Mascarar tokens em logs e UI.
- Validar apenas presenca/nome de variaveis quando necessario.

### Blacklist inicial
- git reset --hard.
- git clean.
- rm -rf e Remove-Item recursivo amplo.
- comandos de deploy sem autorizacao explicita.
- criacao/push de tag sem autorizacao explicita.
- comandos que imprimem env completo.

### Allowlist futura
- Comandos readonly de status, log, diff, leitura limitada e smokes.
- Comandos de build e validacao conhecidos.
- Patches restritos a arquivos esperados por micro.
- Commit e push somente apos suite OK.

### RBAC futuro
- Supervisor pode planejar e aprovar.
- Executor pode rodar comandos permitidos.
- Auditor pode bloquear riscos.
- Docs agent pode ler docs/reports.
- UI deve mostrar permissao requerida antes de executar.

### Smokes futuros
- Bloquear comando destrutivo sem autorizacao.
- Permitir comando readonly seguro.
- Mascarar secret em stdout/stderr.
- Exigir cwd e timeout.
- Rejeitar command_id repetido.
- Confirmar que deploy/tag exigem fluxo separado.

Decisao atual: planejamento apenas. Nenhuma regra runtime, endpoint ou RBAC foi implementado neste micro.

## Implementacao inicial local read-only files 2026-06-14

Status: implementado o helper backend/local_readonly_files.py e o smoke scripts/watcher/smoke_local_readonly_files.py. O smoke foi integrado a smoke_operational_release.py e ao health_report.py.

### Capacidades implementadas
- Leitura read-only de arquivos permitidos.
- Allowlist inicial: docs, reports, scripts/watcher e backend.
- Bloqueio de path traversal.
- Bloqueio de path absoluto.
- Bloqueio de .env e nomes sensiveis.
- Bloqueio de paths com marcadores secret, token, password, passwd, private_key, apikey e api_key.
- Limite de bytes com truncamento controlado.
- Retorno estruturado com ok, path, size, content, truncated e reason.

### Validacoes existentes
- smoke_local_readonly_files.py cobre leitura permitida, arquivo ausente, path traversal, path absoluto, .env bloqueado, marcador sensivel bloqueado, path fora da allowlist e leitura de relatorio.
- smoke_operational_release.py executa o smoke local read-only dentro da suite operacional.
- health_report.py inclui o smoke local read-only no health report.

### Proximos passos
- Evoluir para status/diff read-only.
- Planejar rotas locais GET /local/status, GET /local/diff e GET /local/files/read.
- Manter sem execucao livre de comandos nesta frente ate haver preflight, logs, smokes e UI suficientes.

## Implementacao inicial local repo status 2026-06-14

Status: implementado o helper backend/local_repo_status.py e o smoke scripts/watcher/smoke_local_repo_status.py. O smoke foi integrado a smoke_operational_release.py e ao health_report.py.

### Capacidades implementadas
- Leitura read-only de branch atual.
- Leitura read-only de HEAD curto.
- Leitura read-only de git status --porcelain e git status -sb.
- Lista estruturada de dirty files.
- Leitura read-only de git diff --stat.
- Leitura read-only de git diff --check com return_code preservado.
- Retorno estruturado sem executar comandos arbitrarios fornecidos pelo usuario.

### Validacoes existentes
- smoke_local_repo_status.py valida branch, head, dirty_files, status -sb e retorno de diff-check.
- smoke_operational_release.py executa o smoke local repo status dentro da suite operacional.
- health_report.py inclui o smoke local repo status no health report.

### Proximos passos
- Planejar rotas GET /local/status e GET /local/diff usando estes helpers.
- Manter executor de comandos separado e ainda nao habilitado por API.
- Antes de deploy, repetir suite completa e revisar plataforma real de deploy.

## Implementacao inicial rotas locais read-only 2026-06-14

Status: implementadas rotas FastAPI locais read-only protegidas por admin para diagnostico operacional.

### Rotas implementadas
- GET /local/status: retorna status read-only do repositorio local usando LocalRepoStatus.
- GET /local/diff: retorna diff --stat e diff --check read-only usando LocalRepoStatus.
- GET /local/files/read: le arquivo permitido usando LocalReadonlyFiles com allowlist e bloqueios de secrets/path traversal.

### Seguranca
- Todas as rotas usam Depends(obter_admin_google).
- As rotas nao executam comandos arbitrarios do usuario.
- Leitura de arquivos usa allowlist e bloqueia .env, secrets, tokens, passwords, api keys, path absoluto e traversal.
- Diff/status sao auxiliares de diagnostico, nao executor de comandos.

### Validacoes
- smoke_local_readonly_routes.py valida imports, instancias e guardas admin nas rotas.
- smoke_operational_release.py executa o smoke das rotas dentro da suite operacional.
- health_report.py inclui o smoke das rotas no health report.

### Proximos passos
- Revisar experiencia de UI para consumir estes endpoints.
- Manter deploy/tag apenas com validacao completa imediatamente antes.

## Deploy autorizado executado 2026-06-14

Status: deploy autorizado executado apos validacoes locais e smokes.

### Resultado
- Backend publicado no Railway usando railway up --detach.
- Backend respondeu HTTP 200 no endpoint /status apos deploy.
- Frontend publicado na Vercel em producao usando vercel deploy --prod --yes.
- smoke:prod passou apos deploy.
- Repo permaneceu limpo e alinhado com origin/main.

### Validacoes executadas
- git diff --check.
- py_compile dos modulos diagnosticos.
- smoke_local_readonly_files.
- smoke_local_repo_status.
- smoke_local_readonly_routes.
- smoke_operational_release.
- smoke_health_report.
- npm --prefix frontend run build.
- npm run smoke:prod.

### Observacoes
- Secrets nao foram impressos.
- Deploy e tag continuam separados; nenhuma tag foi criada neste fluxo.
- Proximo passo sugerido: monitorar logs de producao e evoluir UI para consumir as rotas locais read-only.

## 15. Arquitetura de memoria evolutiva e auto-melhoria

A HelpUSAI deve evoluir de chat reativo para agente operacional com estado, memoria, regras, banco, testes e capacidade controlada de alterar codigo, docs e banco usando watcher ou executor interno futuro. A evolucao nao depende de retreinar o modelo a cada uso. O aprendizado deve acontecer por memoria externa, eventos, licoes aprendidas, regras vivas, smokes e tarefas de auto-melhoria.

### 15.1 Referencias conceituais observadas em IAs e agentes existentes

Projetos de IA existentes normalmente combinam chat, mensagens, arquivos, conhecimento, memoria e ferramentas. A HelpUSAI deve ir alem disso e registrar tambem estado operacional, comandos, resultados, erros, licoes, regras, avaliacoes, auto-melhorias e historico de alteracoes.

Padroes uteis para a HelpUSAI:
- Open WebUI como referencia de produto de chat com usuarios, conversas, mensagens, arquivos, conhecimento, funcoes, feedback e permissoes.
- Letta e MemGPT como referencia de memoria hierarquica, com memoria principal e memoria arquivada.
- LangGraph como referencia de persistencia por thread, checkpoints, retomada, human-in-the-loop e tolerancia a falhas.
- CrewAI como referencia de memoria por escopo, importancia, recencia, similaridade e backend vetorial.
- Pesquisas recentes sobre memoria de agentes reforcam que memoria precisa de ingestao, revisao, recuperacao, esquecimento e governanca.

### 15.2 Objetivo da arquitetura HelpUSAI

A HelpUSAI deve se tornar um sistema que registra experiencia, aprende com erros, cria regras, cria testes e melhora o proprio repositorio com micro-alteracoes validadas. O ciclo ideal e: erro vira licao, licao vira regra, regra vira teste, teste vira codigo ou docs, validacao vira commit.

Fluxo alvo:
1. Receber mensagem, comando ou resultado do watcher.
2. Classificar o tipo de evento.
3. Consultar estado persistente, regras e memoria.
4. Decidir se deve ignorar, responder, executar, pedir autorizacao ou propor melhoria.
5. Executar micro pequeno via watcher quando apropriado.
6. Registrar resultado, stdout, stderr, arquivos alterados e validacoes.
7. Extrair licoes aprendidas.
8. Criar ou atualizar regras e smokes.
9. Atualizar docs e memoria.
10. Commitar e pushar somente se as validacoes passarem.

### 15.3 Banco de dados recomendado

A base final recomendada e PostgreSQL com JSONB e, depois, pgvector para busca semantica. Para comecar rapido em ambiente local, SQLite e suficiente, desde que o schema ja seja desenhado para migrar depois.

Tabelas principais recomendadas:

#### agents
Guarda agentes da HelpUSAI, como supervisor, executor, auditor, planner, docs_agent, db_architect, code_editor e release_manager. Campos principais: id, name, role, status, model_provider, model_name, system_prompt, capabilities_json, created_at e updated_at.

#### conversations
Agrupa conversas e fluxos de trabalho. Campos: id, title, project_id, status, current_phase, summary, created_at e updated_at.

#### messages
Registra mensagens entre usuario, agentes e watcher. Campos: id, conversation_id, source_agent_id, target_agent_id, direction, kind, content, metadata_json, status, created_at, read_at e ack_at. Tipos de mensagem: human_instruction, agent_message, watcher_receipt, watcher_error, command_result, decision_request e status_report.

#### agent_state
Estado persistente do agente. Evita loops e perda de contexto. Campos: id, agent_id, project_id, state_json, created_at e updated_at. O state_json deve guardar current_phase, next_micro, ack_loop_closed, last_head, repo_clean, do_not_deploy e pending_human_decision.

#### command_requests
Pedidos de comando feitos pela IA. Campos: id, command_id, requested_by_agent_id, project_id, cwd, command_json, reason, risk_level, status, requires_confirmation, created_at, approved_at, started_at e finished_at.

#### command_results
Resultados estruturados de watcher ou executor interno. Campos: id, command_request_id, return_code, stdout, stderr, files_changed_json, diff_stat, summary e created_at.

#### memories
Memoria operacional e factual. Campos: id, agent_id, project_id, scope, category, content, summary, importance, confidence, source_type, source_id, valid_from, valid_until, created_at e updated_at. Categorias: fact, lesson, preference, workflow_rule, repo_state, error_pattern e decision.

#### lessons
Licoes aprendidas a partir de erros reais. Campos: id, project_id, trigger_event_id, problem, root_cause, lesson, rule_text, severity, status e created_at.

#### rules
Regras vivas que o agente consulta antes de agir. Campos: id, scope, name, rule_text, priority, enabled, source_lesson_id, created_at e updated_at.

#### experience_events
Log bruto de eventos. Campos: id, project_id, agent_id, event_type, input_text, output_text, metadata_json e created_at. Exemplos: user_instruction_received, watcher_ack_received, watcher_error_received, command_failed, command_succeeded, lesson_created, rule_created, test_created, code_modified e migration_proposed.

#### self_improvement_tasks
Fila de melhorias propostas pela propria IA. Campos: id, project_id, title, problem, proposed_solution, target_files_json, risk_level, status, created_by_agent_id, created_at e completed_at. Status: proposed, approved, in_progress, validated, committed e rejected.

#### code_changes
Registro de alteracoes de codigo feitas pela IA. Campos: id, task_id, branch, commit_hash, files_changed_json, diff_summary, validation_json e created_at.

#### db_migrations
Alteracoes de banco propostas ou aplicadas. Campos: id, task_id, migration_name, migration_sql, rollback_sql, status, applied_at e validated_at.

#### evaluations
Smokes e avaliacoes para impedir regressao. Campos: id, project_id, name, type, input_fixture, expected_output, status e last_run_at. Exemplos: smoke_ack_loop_guard, smoke_envelope_parse_error_recovery, smoke_command_id_uniqueness e smoke_supervisor_message.

### 15.4 Memoria por niveis

A HelpUSAI deve separar memoria em quatro niveis:

1. Memoria curta: estado da tarefa atual, arquivos em edicao, ultimo comando e proximo passo.
2. Memoria operacional: regras aprendidas, erros recorrentes, decisoes e padroes seguros.
3. Memoria documental: roadmap, runbooks, relatorios e este documento mestre.
4. Memoria de avaliacao: smokes, fixtures e criterios que impedem repetir erros antigos.

### 15.5 Anti-loop e decisao correta

O agente deve ter uma regra permanente anti-loop: se receber apenas ACK tecnico, nao responder com outro ACK. Se ack_loop_closed for true, qualquer novo ACK deve ser registrado e ignorado, exceto se houver pedido humano novo.

Classificacoes minimas de mensagem:
- human_instruction: pedido novo do usuario.
- watcher_ack: recibo tecnico, normalmente nao responder.
- watcher_error: erro tecnico, analisar e corrigir se for o comando atual.
- command_result_success: resumir resultado e decidir proximo passo.
- command_result_failure: inspecionar status e diff antes de patch.
- loop_ack: registrar e ignorar.
- decision_required: parar e pedir autorizacao humana.

### 15.6 Poder de criar e modificar codigo com watcher

A HelpUSAI pode evoluir alterando codigo, docs e banco usando watcher, mas por micro-alteracoes pequenas e validadas. Niveis de autonomia:

Nivel 1 autonomo: ler arquivos, git status, git diff, atualizar docs, criar smoke simples, corrigir typo, adicionar fixture, rodar validacoes, commit e push de micro pequeno.

Nivel 2 autonomo com validacao forte: alterar backend nao critico, adicionar endpoint interno, criar tabela nova, criar migration reversivel, alterar orquestrador e alterar memoria. Exige py_compile, smoke especifico, smoke_operational_release, smoke_health_report, npm build, git diff --check e rollback quando houver banco.

Nivel 3 decisao humana obrigatoria: deploy, tag release, secrets, apagar dados, migration destrutiva, reset hard, git clean, alteracao de auth, permissao ou producao.

### 15.7 Estrutura inicial recomendada no repo

Arquivos iniciais sugeridos:
- backend/agent_state.py
- backend/agent_message_classifier.py
- backend/experience_learner.py
- backend/ack_loop_guard.py
- backend/self_improvement_planner.py
- backend/evolving_memory.py
- scripts/watcher/send_to_supervisor.py
- scripts/watcher/smoke_agent_state.py
- scripts/watcher/smoke_experience_learner.py
- scripts/watcher/smoke_ack_loop_guard.py
- scripts/watcher/smoke_evolving_memory.py

Arquivos locais ou tabelas iniciais:
- data/helpus/agent_state.json
- data/helpus/memory/events.jsonl
- data/helpus/memory/lessons.md
- data/helpus/memory/rules.json

### 15.8 Proximo micro recomendado

Micro recomendado: HelpUSAI evolving memory database foundation.

Escopo:
1. Criar schema inicial SQLite para agents, messages, agent_state, experience_events, memories, lessons, rules, self_improvement_tasks, command_requests, command_results e evaluations.
2. Criar backend/evolving_memory.py com funcoes simples para registrar evento, criar memoria, criar licao, criar regra, registrar comando, registrar resultado e propor melhoria.
3. Criar smokes para salvar evento, extrair licao, criar regra, impedir loop de ACK, registrar comando watcher, registrar resultado e propor melhoria.
4. Atualizar este documento com qualquer ajuste descoberto.
5. Validar com py_compile, smoke especifico, smoke_operational_release, smoke_health_report, npm build e git diff --check.

### 15.9 Regra de ouro

A HelpUSAI deve sempre transformar uso real em melhoria permanente. Cada erro importante deve gerar uma licao. Cada licao recorrente deve gerar regra. Cada regra critica deve gerar teste. Cada teste deve entrar na suite. Cada melhoria validada deve virar commit pequeno e rastreavel.


## Micro 1 memoria evolutiva aprovado 2026-06-14

Status: iniciado o Micro 1 da arquitetura evolutiva. O objetivo e criar schema local e smoke readonly antes de qualquer autonomia, API ou auto-patch.

### Guardrails aprovados
- Comecar em record_only e suggest_only antes de qualquer execucao automatica.
- Nao integrar ao watcher de producao neste micro.
- Nao executar comandos por API.
- Nao gerar patches automaticos.
- command_requests sao append-only.
- command_results sempre referenciam command_requests.
- stdout e stderr devem ser sanitizados antes de persistencia operacional.
- rules devem evoluir por draft, active, deprecated e rejected.
- db_migrations devem exigir rollback_sql, ambiente e smoke.
- self_restructure_guarded so pode existir com plano, diff, smokes, rollback e gates.

## Roadmap revisado para autosuficiencia HelpUSAI 2026-06-14

Status: revisado apos leitura da documentacao atual e apos conclusao do Micro 1. A resposta anterior continua correta na direcao geral, mas deve ser atualizada para refletir que o schema local e o smoke da memoria evolutiva ja existem.

### Estado atual confirmado
- Micro 1 concluido: backend/evolving_memory_schema.py criado.
- Smoke criado: scripts/watcher/smoke_evolving_memory_schema.py.
- Documentacao atualizada no documento mestre.
- Ainda nao ha integracao com watcher de producao.
- Ainda nao ha execucao por API.
- Ainda nao ha auto-patch automatico.

### O que ainda falta para autosuficiencia real
1. Criar store persistente da memoria evolutiva, inicialmente local, com funcoes append/read para experience_events, command_requests, command_results, lessons, rules e self_improvement_tasks.
2. Registrar eventos readonly do watcher em experience_events com sanitizer de stdout e stderr antes de persistir.
3. Registrar command_requests e command_results de forma append-only e sempre relacionados entre si.
4. Criar extrator de lessons draft a partir de command_results falhos e watcher_errors reais.
5. Promover lessons para rules draft com deduplicacao, prioridade, escopo e status.
6. Criar evaluations e smokes propostos a partir de regras importantes, ainda sem auto-commit.
7. Criar painel/admin readonly para eventos, licoes, regras, comandos e tarefas de auto-melhoria.
8. Habilitar docs_patch_guarded apenas para patches pequenos em docs, com smoke_docs_index e git diff --check.
9. Habilitar code_patch_guarded apenas depois de smokes, allowlist, rollback e auditoria.
10. Habilitar db_migration_guarded somente com rollback_sql, ambiente, smoke e aprovacao humana.
11. Habilitar self_restructure_guarded apenas com plano, diff, smokes, rollback, gates e aprovacao para risco medio ou alto.

### Proximo micro recomendado
Micro 2: EvolvingMemoryStore local e event recorder readonly. Escopo: criar camada simples de persistencia para o schema do Micro 1, gravar experience_events de teste, consultar eventos por projeto e validar via smoke. Nao conectar ainda a API publica, nao executar comandos e nao habilitar auto-patch.

### Definicao atualizada de autosuficiencia
A HelpUSAI sera considerada autosuficiente quando conseguir registrar experiencia, consultar memoria, aprender com falhas, criar lessons, propor rules, gerar smokes, aplicar micro-patches guardados, validar, commitar, auditar, pedir aprovacao por risco e reverter com seguranca. O caminho continua incremental e controlado.
## Micro 2 EvolvingMemoryStore local readonly 2026-06-14

Status: implementado store local inicial para memoria evolutiva, sem API publica, sem execucao de comandos e sem auto-patch.

### Entrega
- backend/evolving_memory_store.py cria EvolvingMemoryStore sobre o schema do Micro 1.
- scripts/watcher/smoke_evolving_memory_store.py valida gravacao e leitura de experience_events em banco local.
- O smoke valida persistencia em disco, filtros por projeto e tipo de evento, limite seguro e ausencia de execucao de comandos/rede no store.

### Limites mantidos
- Ainda nao integrado ao watcher de producao.
- Ainda nao grava eventos reais automaticamente.
- Ainda nao registra command_requests ou command_results automaticamente.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.

### Proximo micro recomendado
Micro 3: event recorder do watcher em modo readonly. Objetivo: transformar entradas ja observadas do watcher em experience_events usando EvolvingMemoryStore, com sanitizer antes de persistir stdout/stderr.

## Micro 3 watcher event recorder readonly 2026-06-14

Status: implementado recorder readonly para transformar eventos observados do watcher em experience_events usando EvolvingMemoryStore.

### Entrega
- backend/evolving_memory_event_recorder.py cria WatcherEventRecorder.
- O recorder normaliza eventos do watcher e grava experience_events.
- Inclui sanitizer inicial para secrets, bearer tokens, chaves e textos longos.
- scripts/watcher/smoke_evolving_memory_event_recorder.py valida redacao, truncamento, persistencia e ausencia de execucao de comandos/rede.

### Limites mantidos
- Ainda nao integrado automaticamente ao watcher de producao.
- Ainda nao registra command_requests ou command_results em tabelas proprias.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 4: command_requests e command_results store. Objetivo: gravar pedidos de comando e resultados de watcher de forma append-only, garantindo que command_results sempre referenciem command_requests.

## Micro 4 command_requests e command_results store 2026-06-14

Status: implementado store local append/read para command_requests e command_results.

### Entrega
- backend/evolving_memory_command_store.py cria EvolvingCommandStore.
- O store grava command_requests com command_id unico, cwd, command_json, reason, risk_level e requires_confirmation.
- O store grava command_results sempre vinculados a command_requests existentes.
- scripts/watcher/smoke_evolving_memory_command_store.py valida duplicidade, integridade referencial, listagens e ausencia de execucao de comandos/rede.

### Limites mantidos
- Ainda nao integrado automaticamente ao watcher de producao.
- Ainda nao grava stdout/stderr reais automaticamente.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 5: sanitizer forte e compartilhado. Objetivo: centralizar redacao de secrets, stdout, stderr, headers, URLs sensiveis e textos longos antes de persistir memoria, command_results ou eventos.
