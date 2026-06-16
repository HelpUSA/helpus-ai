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

## Micro 5 sanitizer forte compartilhado 2026-06-15

Status: implementado sanitizer compartilhado inicial para redacao antes de persistir memoria, eventos e command_results.

### Entrega
- backend/evolving_memory_sanitizer.py centraliza sanitize_text, sanitize_metadata e sanitize_command_result_fields.
- scripts/watcher/smoke_evolving_memory_sanitizer.py valida redacao de API keys, tokens, bearer, authorization, secrets e truncamento de texto longo.
- O sanitizer nao executa comandos, nao importa requests e nao faz rede.

### Limites mantidos
- Ainda precisa ser integrado ao event recorder e command store em micro posterior.
- Ainda nao grava eventos reais automaticamente no watcher de producao.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 6: integrar sanitizer compartilhado ao WatcherEventRecorder e ao EvolvingCommandStore, removendo duplicacao local de sanitize_text e garantindo que stdout/stderr/metadata passem pelo sanitizer antes de persistir.

## Micro 6 integracao do sanitizer compartilhado 2026-06-15

Status: integrado sanitizer compartilhado ao WatcherEventRecorder e ao EvolvingCommandStore.

### Entrega
- backend/evolving_memory_event_recorder.py agora importa sanitize_text e sanitize_metadata de backend/evolving_memory_sanitizer.py.
- backend/evolving_memory_command_store.py agora aplica sanitize_command_result_fields antes de persistir stdout, stderr, diff_stat e summary em command_results.
- Reduzida duplicacao local de sanitizacao e centralizada a politica de redacao.

### Validacoes
- smoke_evolving_memory_sanitizer.py
- smoke_evolving_memory_event_recorder.py
- smoke_evolving_memory_command_store.py
- smoke_evolving_memory_schema.py
- smoke_evolving_memory_store.py
- smoke_docs_index.py
- git diff --check

### Limites mantidos
- Ainda nao integrado automaticamente ao watcher de producao.
- Ainda nao grava command_requests/command_results reais automaticamente.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 7: command/event ingestion adapter readonly. Objetivo: receber envelopes/resultados observados do watcher, gravar experience_events e command_requests/command_results com sanitizer compartilhado, ainda sem execucao automatica e sem API publica.

## Micro 7 command/event ingestion adapter readonly 2026-06-15

Status: implementado ingestion adapter readonly para receber envelopes/resultados observados do watcher e persistir command_requests, command_results e experience_events.

### Entrega
- backend/evolving_memory_ingestion.py cria EvolvingMemoryIngestion.
- scripts/watcher/smoke_evolving_memory_ingestion.py valida ingestao de command request, ingestao de command result, vinculo result->request e rejeicao de resultado orfao.
- O adapter usa WatcherEventRecorder e EvolvingCommandStore, preservando sanitizer compartilhado.
- Nao executa comandos, nao importa requests, nao expoe API publica e nao faz patch.

### Validacoes
- smoke_evolving_memory_ingestion.py
- smoke_evolving_memory_sanitizer.py
- smoke_evolving_memory_event_recorder.py
- smoke_evolving_memory_command_store.py
- smoke_evolving_memory_schema.py
- smoke_evolving_memory_store.py
- smoke_docs_index.py
- git diff --check

### Limites mantidos
- Ainda nao integrado automaticamente ao watcher de producao.
- Ainda nao le fila real do watcher sozinho.
- Ainda nao cria lessons ou rules.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 8: lesson draft extractor readonly. Objetivo: ler command_results/experience_events falhos e gerar lessons em draft com problem, root_cause, lesson, rule_text e severity, sem promover rules automaticamente.

## Micro 8 lesson draft extractor readonly 2026-06-15

Status: implementado extractor readonly para criar lessons em draft a partir de command_results falhos, sem promover rules automaticamente.

### Entrega
- backend/evolving_memory_lesson_extractor.py cria LessonDraftExtractor.
- O extractor classifica falhas comuns: envelope/JSON fragil, SyntaxError/IndentationError e falhas genericas.
- Cria lessons com status draft, problem sanitizado, root_cause, lesson, rule_text e severity.
- scripts/watcher/smoke_evolving_memory_lesson_extractor.py valida classificacao, criacao de draft, sanitizacao, ausencia de lesson para sucesso e limite seguro de listagem.

### Validacoes
- smoke_evolving_memory_lesson_extractor.py
- smoke_evolving_memory_ingestion.py
- smoke_evolving_memory_sanitizer.py
- smoke_evolving_memory_event_recorder.py
- smoke_evolving_memory_command_store.py
- smoke_docs_index.py
- git diff --check

### Limites mantidos
- Ainda nao promove rules automaticamente.
- Ainda nao deduplica lessons.
- Ainda nao le falhas reais automaticamente do watcher de producao.
- Ainda nao executa comandos por API.
- Ainda nao faz auto-patch.

### Proximo micro recomendado
Micro 9: rule draft promoter readonly. Objetivo: promover lessons draft selecionadas para rules draft com deduplicacao por escopo/nome, sem ativar regra automaticamente.

## Micro 9 rule draft promoter readonly 2026-06-15

Status: implementado promoter readonly para transformar lessons draft selecionadas em rules draft, com deduplicacao por scope/name e sem ativar regras automaticamente.

Entrega: backend/evolving_memory_rule_promoter.py e scripts/watcher/smoke_evolving_memory_rule_promoter.py.
Validacoes: rule_promoter, lesson_extractor, ingestion, sanitizer, event_recorder, command_store, docs_index e git diff --check.
Limites: nao ativa rules automaticamente, nao aplica rules em runtime, nao executa comandos por API e nao faz auto-patch.
Proximo micro recomendado: Micro 10 evaluations/smoke proposal generator readonly.

## Micro 10 evaluations smoke proposal generator readonly 2026-06-15

Status: implementado generator readonly para criar evaluations propostas de smoke a partir de rules draft/active, sem executar comandos.
Entrega: backend/evolving_memory_evaluation_proposals.py e scripts/watcher/smoke_evolving_memory_evaluation_proposals.py.
Comportamento: deduplica por project_id/name, cria evaluations status proposed, kind smoke_proposal, target rule_id e command_json proposto.
Validacoes: evaluation_proposals, rule_promoter, lesson_extractor, ingestion, sanitizer, event_recorder, command_store e git diff --check.
Limites: nao executa smoke proposto, nao ativa rules, nao aplica rules em runtime e nao faz auto-patch.
Proximo micro recomendado: Micro 11 readonly memory report/export para resumir rules, lessons, evaluations e command history em relatorio local.

## Micro 11 readonly memory report/export 2026-06-15

Status: implementado report/export readonly para gerar snapshot local da evolving memory sem executar comandos.
Entrega: backend/evolving_memory_report.py e scripts/watcher/smoke_evolving_memory_report.py.
Comportamento: gera snapshot com counts, rules, lessons, evaluations, command_requests e failed_command_results; renderiza Markdown e exporta JSON.
Validacoes: memory_report, evaluation_proposals, rule_promoter, lesson_extractor, ingestion, sanitizer, event_recorder, command_store, docs_index e git diff --check.
Limites: nao executa comandos, nao altera runtime, nao ativa rules, nao aplica rules e nao faz auto-patch.
Proximo micro recomendado: Micro 12 readonly operator dashboard summary para consolidar status operacional e proximas acoes seguras.

## Micro 12 readonly operator dashboard summary concluido - 2026-06-15

Entrega:
- Criado `backend/evolving_memory_operator_dashboard.py`.
- Criado `scripts/watcher/smoke_evolving_memory_operator_dashboard.py`.
- Dashboard operacional somente leitura para consolidar status, contagens, itens recentes, falhas recentes e proximas acoes seguras.

Comportamento:
- Consulta SQLite em modo readonly logico.
- Nao executa comandos.
- Nao usa rede externa.
- Nao cria API publica.
- Nao ativa rules automaticamente.
- Nao altera dados de memoria.

Validacoes:
- `python -m py_compile backend/evolving_memory_operator_dashboard.py scripts/watcher/smoke_evolving_memory_operator_dashboard.py`
- `python scripts/watcher/smoke_evolving_memory_operator_dashboard.py`
- Smokes base da evolving memory.
- `python scripts/watcher/smoke_docs_index.py`
- `git diff --check`

Limites:
- Qualquer falha deve parar o fluxo e reportar stdout/stderr.
- Rules e lessons continuam dependendo de gate humano.
- O dashboard e apenas apoio operacional para leitura e decisao.

Proximo micro recomendado:
- Micro 13 HelpUSAI operational context card para reduzir alucinacao operacional e melhorar conversa/comandos seguros.

## Micro 13 HelpUSAI operational context card concluido - 2026-06-15

Entrega:
- Criado docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md.
- Criado backend/helpus_operational_context_card.py.
- Criado scripts/watcher/smoke_helpus_operational_context_card.py.

Objetivo:
- Reduzir alucinacao operacional da HelpUSAI.
- Garantir que a IA reconheca repo, ambiente, micro atual, comandos readonly, allowlist, smokes e restricoes.
- Fornecer um prompt compacto reutilizavel antes de planejamento de comandos.

Comportamento:
- Card readonly e conservador.
- Nao executa comandos.
- Nao usa rede externa.
- Nao ativa rules automaticamente.
- Nao cria API publica.

Validacoes:
- python -m py_compile backend/helpus_operational_context_card.py scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- git diff --check

Proximo micro recomendado:
- Micro 14 Safe Command Planner para transformar intencoes do usuario em comandos seguros com allowlist, timeout, cwd e stop-on-failure.

## Micro 14 Safe Command Planner concluido - 2026-06-15

Entrega:
- Criado backend/helpus_safe_command_planner.py.
- Criado scripts/watcher/smoke_helpus_safe_command_planner.py.

Objetivo:
- Transformar intencoes do usuario em planos de comandos seguros.
- Sempre incluir cwd, timeout, comandos, risco, allowlist, validacoes e stop-on-failure.
- Bloquear comandos perigosos antes de qualquer execucao.

Comportamento:
- Planner readonly: nao executa comandos.
- Usa HelpUSOperationalContextCard como fonte de contexto.
- Classifica status/inspecao, smokes, Micro 14 patch, desconhecido e comandos perigosos.
- Comandos perigosos retornam plano blocked sem comandos.

Validacoes:
- python -m py_compile backend/helpus_safe_command_planner.py scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- git diff --check

Proximo micro recomendado:
- Micro 15 Approval Gate para separar execucao automatica bloqueada, execucao readonly permitida e patch com aprovacao humana.

## Micro 15 Approval Gate concluido - 2026-06-15

Entrega:
- Criado backend/helpus_approval_gate.py.
- Criado scripts/watcher/smoke_helpus_approval_gate.py.
- Atualizado badge visual temporario para v0.15.0-dev.

Objetivo:
- Separar planos readonly permitidos, planos que exigem aprovacao humana e planos bloqueados.
- Impedir que comandos perigosos avancem para execucao.
- Manter stop-on-failure como comportamento padrao.

Comportamento:
- Gate readonly: nao executa comandos.
- Avalia planos gerados pelo Safe Command Planner.
- Low risk sem arquivos vira readonly_allowed.
- Medium/review/arquivos vira approval_required.
- Blocked ou dangerous tokens vira blocked sem comandos.

Validacoes:
- python -m py_compile backend/helpus_approval_gate.py scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Micro 16 Command Execution Envelope Builder para converter planos aprovados em envelopes/comandos revisaveis sem executar automaticamente.

## Micro 16 Command Execution Envelope Builder concluido - 2026-06-15

Entrega:
- Criado backend/helpus_execution_envelope_builder.py.
- Criado scripts/watcher/smoke_helpus_execution_envelope_builder.py.
- Atualizado badge visual temporario para v0.16.0-dev.

Objetivo:
- Converter planos e decisoes aprovadas em envelopes revisaveis.
- Nao executar comandos automaticamente.
- Separar envelopes readonly permitidos, approval-required e blocked.

Comportamento:
- Builder readonly: nao chama subprocess, rede ou APIs externas.
- readonly_allowed gera reviewable-run-command.
- approval_required gera reviewable-approval-required.
- blocked gera envelope blocked sem comandos.
- Todo envelope inclui warnings e stop-on-failure.

Validacoes:
- python -m py_compile backend/helpus_execution_envelope_builder.py scripts/watcher/smoke_helpus_execution_envelope_builder.py
- python scripts/watcher/smoke_helpus_execution_envelope_builder.py
- python scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Micro 17 Conversation Response Composer para transformar planos, gates e envelopes em respostas curtas da HelpUSAI.

## Micro 17 Conversation Response Composer concluido - 2026-06-15

Entrega:
- Criado backend/helpus_conversation_response_composer.py.
- Criado scripts/watcher/smoke_helpus_conversation_response_composer.py.
- Atualizado badge visual temporario para v0.17.0-dev.

Objetivo:
- Transformar contexto, plano, gate e envelope em respostas curtas da HelpUSAI.
- Melhorar a conversa antes de qualquer execucao.
- Explicar repo, risco, decisao, acao, comandos, arquivos, avisos e proximo passo.

Comportamento:
- Composer readonly: nao executa comandos.
- Usa Operational Context Card, Safe Command Planner, Approval Gate e Envelope Builder.
- readonly_allowed mostra comandos sugeridos e regra de parada.
- approval_required pede aprovacao humana.
- blocked informa que nao deve executar.

Validacoes:
- python -m py_compile backend/helpus_conversation_response_composer.py scripts/watcher/smoke_helpus_conversation_response_composer.py
- python scripts/watcher/smoke_helpus_conversation_response_composer.py
- python scripts/watcher/smoke_helpus_execution_envelope_builder.py
- python scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Micro 18 Conversation API Adapter para expor o composer internamente ao fluxo de chat sem executar comandos.

## Micro 18 Conversation API Adapter concluido - 2026-06-15

Entrega:
- Criado backend/helpus_conversation_api_adapter.py.
- Criado scripts/watcher/smoke_helpus_conversation_api_adapter.py.
- Atualizado badge visual temporario para v0.18.0-dev.

Objetivo:
- Adaptar mensagens do chat para o composer quando houver intencao operacional.
- Nao executar comandos automaticamente.
- Permitir que mensagens normais sigam para o modelo principal sem interceptacao.

Comportamento:
- Adapter readonly: nao chama subprocess, rede ou APIs externas.
- Detecta intencoes de comandos, smokes, repo, patch e micros.
- Usa Conversation Response Composer para gerar resposta operacional curta.
- Retorna flags de seguranca para execucao, rede, arquivos, revisao e stop-on-failure.

Validacoes:
- python -m py_compile backend/helpus_conversation_api_adapter.py scripts/watcher/smoke_helpus_conversation_api_adapter.py
- python scripts/watcher/smoke_helpus_conversation_api_adapter.py
- python scripts/watcher/smoke_helpus_conversation_response_composer.py
- python scripts/watcher/smoke_helpus_execution_envelope_builder.py
- python scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Micro 19 Chat Endpoint Wiring guarded para conectar o adapter ao endpoint real de chat com flag desligada por padrao.

## Micro 19 Chat Endpoint Wiring guarded concluido - 2026-06-15

Entrega:
- Criado backend/helpus_chat_endpoint_wiring.py.
- Criado scripts/watcher/smoke_helpus_chat_endpoint_wiring.py.
- Atualizado badge visual temporario para v0.19.0-dev.

Objetivo:
- Conectar o Conversation API Adapter ao fluxo de chat por uma camada guardada.
- Manter a feature flag desligada por padrao.
- Preservar resposta principal quando o adapter estiver desligado ou nao reconhecer intencao operacional.

Comportamento:
- Wiring readonly: nao executa comandos.
- Default enabled=False.
- Mensagens normais preservam a resposta primaria.
- Mensagens operacionais usam adapter apenas quando enabled=True.
- Mensagens perigosas continuam blocked e sem execucao.

Validacoes:
- python -m py_compile backend/helpus_chat_endpoint_wiring.py scripts/watcher/smoke_helpus_chat_endpoint_wiring.py
- python scripts/watcher/smoke_helpus_chat_endpoint_wiring.py
- python scripts/watcher/smoke_helpus_conversation_api_adapter.py
- python scripts/watcher/smoke_helpus_conversation_response_composer.py
- python scripts/watcher/smoke_helpus_execution_envelope_builder.py
- python scripts/watcher/smoke_helpus_approval_gate.py
- python scripts/watcher/smoke_helpus_safe_command_planner.py
- python scripts/watcher/smoke_helpus_operational_context_card.py
- python scripts/watcher/smoke_evolving_memory_operator_dashboard.py
- python scripts/watcher/smoke_docs_index.py
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Micro 20 Minimal guarded endpoint integration para plugar o wiring no endpoint real atras de variavel de ambiente desligada por padrao.


## Micros 20 a 22 Runtime guarded batch concluido - 2026-06-15

Entrega:
- Criado backend/helpus_runtime_feature_flags.py.
- Criado backend/helpus_chat_runtime_adapter.py.
- Criado backend/helpus_operator_visibility.py.
- Criados smokes de runtime flags, runtime adapter e operator visibility.
- Atualizado badge visual temporario para v0.22.0-dev.

Objetivo:
- Agrupar feature flags runtime, adapter runtime guardado e visibilidade operacional.
- Manter adapter desligado por padrao.
- Preparar caminho para integracao real com endpoint sem alterar comportamento atual.

Comportamento:
- Runtime flags leem HELPUSAI_CONVERSATION_ADAPTER_ENABLED e HELPUSAI_CONVERSATION_ADAPTER_FORCE.
- Default seguro: adapter disabled.
- Runtime adapter preserva resposta primaria quando desligado.
- Operator visibility mostra versao, micros, flags e seguranca.

Validacoes:
- python scripts/watcher/smoke_helpus_runtime_feature_flags.py
- python scripts/watcher/smoke_helpus_chat_runtime_adapter.py
- python scripts/watcher/smoke_helpus_operator_visibility.py
- cadeia completa dos smokes de conversa e seguranca.
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Batch B Micros 23 a 25: dry-run real de conversa, command envelope export e readonly execution gate.


## Micros 23 a 25 Dry-run envelope readonly gate concluido - 2026-06-15

Entrega:
- Criado backend/helpus_conversation_dry_run.py.
- Criado backend/helpus_command_envelope_export.py.
- Criado backend/helpus_readonly_execution_gate.py.
- Criados smokes de dry-run, envelope export e readonly execution gate.
- Atualizado badge visual temporario para v0.25.0-dev.

Objetivo:
- Validar conversa operacional em modo dry-run.
- Exportar envelopes revisaveis em JSON/Markdown.
- Permitir somente avaliacao de comandos readonly; sem executar automaticamente.

Comportamento:
- Dry-run testa mensagens normais, status, smokes, dangerous e force adapter.
- Envelope export gera payload revisavel.
- Readonly gate permite apenas comandos git/status/diff/log, py_compile e smokes.
- Readonly gate nunca executa comandos; apenas decide.

Validacoes:
- python scripts/watcher/smoke_helpus_conversation_dry_run.py
- python scripts/watcher/smoke_helpus_command_envelope_export.py
- python scripts/watcher/smoke_helpus_readonly_execution_gate.py
- cadeia completa dos smokes de conversa e seguranca.
- npm --prefix frontend run build
- git diff --check

Proximo micro recomendado:
- Batch C Micros 26 a 29: patch proposal mode, human-approved patch apply, guarded memory feedback e final release readiness.


## Micros 26 a 29 Final guarded release batch concluido - 2026-06-15

Entrega:
- Criado backend/helpus_patch_proposal_mode.py.
- Criado backend/helpus_human_approved_patch_apply.py.
- Criado backend/helpus_guarded_memory_feedback.py.
- Criado backend/helpus_final_release_readiness.py.
- Criados smokes de patch proposal, human-approved patch apply, guarded memory feedback e final release readiness.
- Atualizado badge visual temporario para v0.29.0-dev.

Objetivo:
- Fechar a cadeia operacional segura da HelpUSAI.
- Permitir proposta de patch sem aplicar automaticamente.
- Modelar aplicacao de patch somente com aprovacao humana e allowlist.
- Registrar feedback de memoria apenas como draft, sem promover rules automaticamente.
- Consolidar checklist final de release readiness.

Comportamento:
- Patch proposal mode e reviewable only.
- Human-approved patch apply retorna decisao; nao aplica agora.
- Guarded memory feedback e draft_only.
- Final readiness permanece ready_for_release=False ate revisao humana final.
- Deploy continua proibido sem aprovacao explicita.

Validacoes:
- python scripts/watcher/smoke_helpus_patch_proposal_mode.py
- python scripts/watcher/smoke_helpus_human_approved_patch_apply.py
- python scripts/watcher/smoke_helpus_guarded_memory_feedback.py
- python scripts/watcher/smoke_helpus_final_release_readiness.py
- cadeia completa dos smokes HelpUSAI.
- npm --prefix frontend run build
- git diff --check

Estado final esperado:
- HelpUSAI entende contexto, planeja comandos, classifica risco, bloqueia perigosos, gera envelopes, faz dry-run, avalia readonly, propoe patches, exige aprovacao humana e prepara release readiness.

## Micro 30 - Persistent memory schema and API draft

Status: completed as guarded local persistence foundation.

Resumo:
- Adicionado schema versionado para memoria persistente da HelpUSAI.
- Adicionado store local sqlite para smokes e validacao inicial.
- Adicionado API router draft sem wiring automatico em producao.
- Atualizado badge visual temporario para v0.30.0-dev.

Validacoes:
- smoke_helpus_persistent_memory_schema.py
- smoke_helpus_persistent_memory_store.py
- smoke_helpus_persistent_memory_api.py
- smoke_docs_index.py
- frontend build

Proximo micro recomendado: Micro 31 Railway Postgres migration plan and guarded apply script.

## Micro 32 - Controlled Railway Postgres memory migration apply

Status: completed with manual Railway SSH apply and readonly verification.

Resumo:
- Aplicada migration additive-only da memoria persistente no Railway Postgres.
- Aplicacao feita dentro do container helpus-api via railway ssh.
- Confirmadas tabelas helpus_memory_events, helpus_memory_feedback, helpus_memory_lessons e helpus_memory_rules.
- Confirmados 13 indices nas tabelas de memoria.
- Atualizado badge visual temporario para v0.32.0-dev.

Validacoes:
- readonly table verification
- smoke_helpus_memory_postgres_migration_sql.py
- smoke_helpus_memory_migration_apply_guard.py
- smokes de memoria persistente Micro 30
- smoke_docs_index.py
- frontend build

Proximo micro recomendado: Micro 33 guarded production memory API wiring with admin protection.

## 2026-06-16 - Roadmap adicional: ferramenta de pesquisa de codigo externo

Contexto: durante a retomada da evolucao da HelpUSAI, foi identificada uma oportunidade de tornar a assistente mais agil para tarefas tecnicas usando uma capacidade consultiva de pesquisa de codigo externo. A ideia nao substitui a analise do repositorio local D:/dev/ai e nao deve aplicar codigo automaticamente. Ela deve servir como apoio para comparar padroes publicos, encontrar exemplos reais e melhorar propostas tecnicas antes de qualquer patch.

A funcionalidade proposta pode consultar mecanismos como grep.app, GitHub Code Search ou fontes equivalentes de pesquisa de codigo publico. O objetivo e permitir que a HelpUSAI pesquise exemplos de FastAPI, Postgres, psycopg, memoria persistente, migrations, fallback de providers e padroes de arquitetura similares. Os resultados devem virar resumo tecnico, riscos e proposta adaptada ao nosso repositorio, nunca copia direta de codigo externo.

Regra central: a fonte da verdade continua sendo o repositorio local D:/dev/ai, o banco Railway Postgres e os documentos consolidados em docs. A pesquisa externa e apenas consultiva. Qualquer resultado externo precisa ser interpretado, adaptado, validado por smoke e aprovado antes de virar codigo.

Contrato recomendado para a ferramenta HelpUSAI Code Research Tool: entrada com objetivo tecnico, linguagem, framework, termos de busca e arquivos locais relevantes; saida com resumo dos padroes encontrados, links ou referencias, riscos de licenca e seguranca, sugestao adaptada ao repo e lista de validacoes. A ferramenta nao deve executar patch automatico, nao deve promover regra sozinha e nao deve gravar codigo bruto copiado como memoria.

Ordem recomendada de evolucao: primeiro concluir o recorder interno de memoria; depois ligar o recorder no /chat com flag; depois criar leitura de memoria; depois injetar memoria resumida no prompt; depois criar ferramenta de pesquisa de codigo; por fim guardar na memoria apenas decisoes aprovadas, padroes validados e licoes confirmadas.

Impacto esperado: reduzir tempo de investigacao tecnica, melhorar a qualidade dos patches, ajudar a HelpUSAI a comparar abordagens reais e diminuir tentativa e erro. Risco principal: copiar padroes inadequados ou codigo externo sem contexto. Mitigacao: sempre exigir resumo, adaptacao local, smoke, diff pequeno e aprovacao humana.

Decisao operacional: manter apenas este arquivo como documentacao detalhada de roadmap/historico em docs. Relatorios pequenos podem existir para marcos especificos, mas o historico textual e as atividades futuras devem ser consolidados aqui sempre que possivel.

## 2026-06-16 - Roadmap adicional: ferramenta de inspecao de webhooks

Contexto: alem da ferramenta consultiva de pesquisa de codigo externo, foi identificada outra capacidade util para a HelpUSAI: uma ferramenta de inspecao de webhooks e callbacks externos. A referencia operacional sugerida e webhook.site ou servico equivalente. Essa capacidade nao deve ser tratada como memoria, nem como dependencia de producao. Ela deve servir para observabilidade, depuracao e desenho seguro de integracoes.

Objetivo: permitir que a HelpUSAI ajude a testar chamadas HTTP recebidas de servicos externos antes de implementar endpoints reais no backend. Exemplos de uso incluem callbacks de GitHub, Railway, Stripe, formularios, automacoes, ferramentas internas e futuros fluxos de integracao. O valor principal e enxergar metodo, headers, body, user-agent, timestamp e formato real do payload enviado pelo servico emissor.

Regra central: webhook.site deve ser usado apenas para testes com dados nao sensiveis. Nao enviar PHI, documentos pessoais, tokens, senhas, API keys, dados de clientes, payloads privados ou informacoes reguladas. A ferramenta nao deve armazenar conhecimento permanente e nao deve virar componente obrigatorio da HelpUSAI em producao. Logs oficiais, Railway, banco Postgres e endpoints proprios continuam sendo as fontes reais do sistema.

Contrato recomendado para a ferramenta HelpUSAI Webhook Inspection Tool: entrada com objetivo do teste, servico emissor, URL temporaria de inspecao, payload esperado e avaliacao de risco de privacidade; saida com resumo do payload recebido, headers importantes, campos necessarios para endpoint real, riscos de seguranca, sugestao de contrato FastAPI e smokes de validacao. A ferramenta deve orientar e documentar, mas nao deve criar endpoint produtivo sem aprovacao humana.

Uso esperado no fluxo de desenvolvimento: primeiro apontar o servico externo para uma URL temporaria de inspecao; depois observar o payload real; depois desenhar o schema interno; depois criar endpoint local pequeno; depois testar com smoke; por fim trocar a URL temporaria pelo endpoint oficial da HelpUSAI somente quando houver seguranca e validacao.

Limites de seguranca: nunca colar segredos em webhook.site; nunca usar payload real sensivel; nunca depender de URL temporaria como storage; nunca transformar request recebida em acao automatica sem autenticacao, assinatura, replay protection e validacao de origem. Todo webhook produtivo deve ter validacao explicita, logs seguros e tratamento de erro sem vazamento de segredo.

Ordem recomendada no roadmap: concluir primeiro recorder interno de memoria, ligar recorder no chat, criar leitura de memoria, injetar memoria segura no prompt, implementar ferramenta consultiva de pesquisa de codigo, e entao implementar ferramenta de inspecao de webhooks. Depois disso, avancar para promocao controlada de lessons e rules e limpeza ou deduplicacao de memoria.

Impacto esperado: acelerar integracoes externas, reduzir tentativa e erro em callbacks, melhorar o desenho de endpoints e aumentar confianca antes de expor rotas reais. Risco principal: vazamento de dados sensiveis ou uso indevido de URL temporaria. Mitigacao: politica de dados sinteticos, revisao humana, checklist de seguranca e proibicao de segredos em ferramentas externas.

## 2026-06-16 - Roadmap adicional: ferramenta de prototipacao visual com v0.dev

Contexto: depois da pesquisa consultiva de codigo externo e da inspecao segura de webhooks, foi identificada uma terceira capacidade futura para a HelpUSAI: uma ferramenta consultiva de prototipacao visual e geracao assistida de interfaces usando v0.dev ou plataforma equivalente. A finalidade e acelerar desenho de telas, dashboards e componentes, sem aplicar codigo automaticamente no repositorio.

Objetivo: permitir que a HelpUSAI transforme descricoes de fluxos, telas e necessidades operacionais em prototipos visuais, componentes React, layouts Tailwind e propostas de UX. Usos esperados incluem painel de memorias, feedbacks, lessons, rules candidatas, auditoria de decisoes, painel de integracoes, painel de webhooks, dashboard de saude dos providers e telas administrativas da propria HelpUSAI.

Regra central: v0.dev deve ser tratado como ferramenta de exploracao visual, nao como fonte da verdade do projeto. A fonte da verdade continua sendo D:/dev/ai, os componentes existentes, o design system real, os smokes locais, o build do frontend e os criterios de seguranca. Codigo gerado externamente deve ser considerado rascunho, revisado, reduzido, adaptado ao padrao local e validado antes de qualquer commit.

Contrato recomendado para a HelpUSAI UI Prototyping Tool: entrada com objetivo da tela, usuario alvo, fluxo esperado, stack do projeto, componentes existentes, restricoes visuais, estados de carregamento e erro, requisitos de acessibilidade e screenshot ou mockup opcional; saida com proposta de tela, componentes sugeridos, codigo de referencia, riscos de integracao, arquivos provaveis a alterar e checklist de build, smoke e revisao visual.

Limites de seguranca: nao enviar dados sensiveis, segredos, informacoes de clientes, PHI, tokens, credenciais ou dumps internos para ferramentas externas de prototipacao. Nao aceitar deploy automatico, nao aceitar dependencias novas sem revisao, nao alterar backend, autenticacao, banco ou rotas produtivas por sugestao visual. A ferramenta deve apoiar UX e UI, nao substituir revisao humana.

Ordem recomendada no roadmap: concluir recorder interno de memoria, ligar recorder no chat, criar leitura de memoria, injetar memoria segura no prompt, implementar pesquisa consultiva de codigo, implementar inspecao segura de webhooks e entao implementar prototipacao visual com v0.dev. A implementacao deve ser consultiva, orientada por checklist e validada por build/smoke antes de merge.

Impacto esperado: acelerar criacao de telas, reduzir custo de experimentacao visual, melhorar comunicacao de UX, aumentar precisao na construcao de paineis administrativos e permitir que a HelpUSAI proponha interfaces mais claras antes de mexer no codigo produtivo.

## 2026-06-16 - Item 1 concluido: recorder interno de memoria

Contexto: foi concluida a primeira parte tecnica da memoria persistente da HelpUSAI. O recorder interno foi criado como modulo isolado, seguro por padrao e sem exposicao publica. Ele prepara o caminho para gravar eventos de conversa em helpus_memory_events depois que o wiring no /chat for implementado.

Arquivo principal criado: backend/helpus_internal_memory_recorder.py. O modulo define HELPUS_MEMORY_RECORDING_ENABLED como flag de ativacao, usa helpus_chat_runtime como source e fornece funcoes para compactar texto, montar summary, montar details em JSON, mascarar DATABASE_URL e gravar eventos no Postgres quando a flag estiver ligada e uma URL de banco estiver disponivel.

Comportamento de seguranca: por padrao o recorder fica desligado. Sem HELPUS_MEMORY_RECORDING_ENABLED=1 ele retorna skipped com reason recording_disabled. Com a flag ligada mas sem DATABASE_URL, POSTGRES_URL ou DATABASE_PUBLIC_URL, ele retorna skipped com reason database_url_missing. A funcao safe_record_chat_memory_event captura erros e retorna skipped em vez de derrubar o fluxo do chat.

Limites importantes: este item nao liga o recorder no /chat, nao cria API publica, nao promove feedback automaticamente, nao cria lessons automaticamente e nao cria rules automaticamente. Os campos automatic_feedback_promotion, automatic_lesson_promotion e automatic_rule_promotion ficam explicitamente False no payload de details e no status do recorder.

Smoke permanente criado: scripts/helpusai/smoke_internal_memory_recorder.py. O smoke valida que o recorder fica desligado por padrao, nao quebra sem banco, compacta summaries, mascara segredos da URL do banco e preserva as travas contra promocao automatica.

Status do roadmap de memoria: Item 1 concluido como fundacao local. Proximo passo recomendado: Item 2, inspecionar o runtime do /chat e ligar safe_record_chat_memory_event somente depois de uma resposta bem-sucedida, atras da mesma flag HELPUS_MEMORY_RECORDING_ENABLED.

## 2026-06-16 - Item 2 concluido: recorder ligado ao chat

Contexto: o recorder interno de memoria foi ligado ao endpoint principal /chat depois da geracao bem-sucedida da resposta. A integracao usa safe_record_chat_memory_event e roda por run_in_threadpool para evitar bloquear diretamente o fluxo async do FastAPI.

Arquivo alterado: backend/main.py. A chamada acontece depois de cerebro.pensar produzir resposta, tokens e tempo_ia, e antes do retorno MensagemResponse. O recorder recebe user_message, assistant_reply, conversation_id, provider, route chat, project_id e metadados leves como tokens_gerados, tempo_ia e quantidade de fontes. A integracao nao armazena email do usuario no details do evento.

Seguranca operacional: a gravacao continua desligada por padrao e so grava quando HELPUS_MEMORY_RECORDING_ENABLED=1 e uma URL de banco estiver configurada. Sem flag ou sem banco, o recorder retorna skipped. Qualquer erro interno de gravacao e capturado pelo safe_record_chat_memory_event e nao deve derrubar a conversa.

Smoke permanente criado: scripts/helpusai/smoke_chat_memory_wiring.py. O smoke valida imports, chamada via run_in_threadpool, mapeamento de campos essenciais e ordem correta: resposta gerada primeiro, recorder chamado depois, MensagemResponse retornado por ultimo.

Status do roadmap de memoria: Item 2 conclui o wiring basico do recorder no /chat. Proximos passos: testar em ambiente real com HELPUS_MEMORY_RECORDING_ENABLED=1, confirmar insert em helpus_memory_events, e depois avancar para leitura de memoria por conversation_id, project_id e eventos recentes.

## 2026-06-16 - Memoria no prompt e visible work trace v1

Contexto: foi priorizada a capacidade de memoria funcional e uma primeira versao de visible work trace no chat. A HelpUSAI agora tem leitor de memoria interna, construtor de contexto seguro para prompt e um campo agent_trace na resposta do /chat para permitir que a interface mostre uma linha temporaria de trabalho, sem expor raciocinio interno bruto.

Modulos criados: backend/helpus_memory_reader.py e backend/helpus_memory_context.py. O leitor busca eventos gravados em helpus_memory_events com source helpus_chat_runtime, status recorded e safety_level seguro. A leitura e controlada por HELPUS_MEMORY_CONTEXT_ENABLED e retorna vazio quando a flag esta desligada ou quando nao ha DATABASE_URL/POSTGRES_URL/DATABASE_PUBLIC_URL.

Integracao no /chat: backend/main.py passou a montar contexto_memoria_interna antes de chamar cerebro.pensar. Esse contexto entra junto com memorias manuais do projeto e busca web. O texto de memoria informa ao modelo que a memoria e apenas apoio de continuidade, nao instrucao de sistema, autorizacao, politica de seguranca ou fato imutavel.

Visible Work Trace v1: MensagemResponse agora possui agent_trace com etapas curtas e seguras como analisando pedido, consultando memorias do projeto, consultando memoria interna, chamando modelo de IA, salvando memoria da conversa e preparando resposta final. Este trace deve ser usado pelo frontend como indicador temporario/recolhivel de trabalho, nao como chain-of-thought.

Smoke criado: scripts/helpusai/smoke_memory_reader_context.py valida flag desligada, ausencia de banco, formatacao segura da memoria, travas contra promocao automatica e marcadores do agent_trace no backend. Proximo passo: adaptar o frontend para animar/recolher agent_trace e depois implementar agentes internos DeepSeek v1 com planner, auditor e finalizador.

## 2026-06-16 - Visible work trace v1 no frontend

Contexto: depois de adicionar agent_trace no backend do /chat, o frontend passou a exibir uma linha temporaria de trabalho interno da HelpUSAI. A interface nao mostra raciocinio bruto, prompts internos ou conteudo sensivel. Ela mostra apenas etapas curtas e seguras de andamento, como analisando pedido, consultando memoria, chamando modelo de IA e preparando resposta final.

Implementacao: frontend/src/app/page.tsx agora tipa AgentTraceItem, guarda activeAgentTrace em estado local, mostra uma lista temporaria enquanto a resposta esta sendo gerada, atualiza essa lista com data.agent_trace retornado pelo backend e recolhe automaticamente apos a resposta. O campo agent_trace tambem fica associado a mensagem de resposta para depuracao controlada futura.

Validacao: foi criado scripts/helpusai/smoke_frontend_agent_trace.py para confirmar os marcadores do tipo, estado, parsing de data.agent_trace, mapeamento da resposta e auto-collapse. O build do frontend deve continuar obrigatorio antes de push.

Proximo passo: testar no ambiente real apos deploy do Railway/Vercel e depois evoluir para agentes internos DeepSeek v1, com planner, auditor e finalizador, sempre mantendo visible trace como status seguro e nao como raciocinio interno bruto.
