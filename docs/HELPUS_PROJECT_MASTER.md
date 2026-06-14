# HelpUS - Documento Mestre do Projeto

Este documento unifica a documentacao operacional do projeto HelpUS AI. Os documentos anteriores foram preservados em docs/legacy para consulta historica.

## Estado consolidado

- Repo principal: D:/dev/ai
- Branch principal: main
- Remoto principal: origin/main
- Execucao local: watcher / AI Bridge Local
- Regra central: executar via watcher, validar com smokes/build/diff-check e nao fazer deploy sem autorizacao explicita.

## O que ja foi feito

- Documentada a operacao segura do agente HelpUS.
- Documentado o protocolo de comandos watcher.
- Documentada a automacao operacional e health report.
- Criado roadmap de inteligencia do chat watcher com micros 24 a 29.
- Documentada a frente de provedor local/offline de IA.
- Micro 24 concluido com backend/operational_context.py e scripts/watcher/smoke_operational_context.py.
- Micro 25 concluido com backend/watcher_intent.py e scripts/watcher/smoke_watcher_intent.py.
- Micro 26 avancou com smoke de envelope builder baseado em backend/command_builder.py.
- Micro 27 foi iniciado, mas ainda precisa ser concluido e validado.

## Atividades pendentes detalhadas

### 1. Concluir Micro 27 - Recuperacao de erros watcher

- Corrigir e validar backend/watcher_recovery.py.
- Criar/validar scripts/watcher/smoke_watcher_recovery.py.
- Integrar o smoke na suite operacional e no health report.
- Garantir tratamento de envelope_parse_error, return_code diferente de zero, erro de build, erro de smoke e erro de git diff --check.
- Validar com py_compile, smoke especifico, smoke_operational_release, smoke_health_report, build frontend e git diff --check.

### 2. Concluir Micro 28 - Integracao com resposta do chat

- Conectar operational_context, watcher_intent, CommandBuilder/envelope builder e watcher_recovery no fluxo real de resposta.
- Diferenciar pedido novo, recibo de sucesso, recibo de erro e acao sensivel.
- Em erro de parse, nunca repetir o envelope; gerar command_id novo e comando mais simples.
- Em falha parcial, inspecionar antes de corrigir.

### 3. Concluir Micro 29 - Provedor local/offline de IA

- Implementar backend/local_ai_provider.py opcional e seguro por padrao.
- Usar HELPUS_LOCAL_AI_ENABLED, HELPUS_LOCAL_AI_BASE_URL, HELPUS_LOCAL_AI_MODEL e HELPUS_LOCAL_AI_TIMEOUT_SECONDS.
- Nao quebrar a aplicacao se o runtime local estiver indisponivel.
- Usar IA local apenas para analise; execucao continua via watcher.

### 4. Regras permanentes

- Nao tratar [AI_LOCAL], [AI_LOCAL_RUN] ou [AI_LOCAL_ERRO] como novo comando do usuario.
- Nao usar git reset --hard, git clean, remocoes em massa, migracoes destrutivas ou alteracao de secrets sem dry-run e autorizacao.
- Nao fazer deploy sem autorizacao explicita.
- Nao commitar alteracoes inesperadas fora do escopo.

## Validacoes recomendadas

powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check


## Fontes legacy unificadas


---

## Fonte legacy: HELPUS_AGENT_OPERATING_PROTOCOL.md

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


---

## Fonte legacy: HELPUS_AI_BRIDGE_OPERATIONS_2026-06-12.md

# HelpUS AI e AI Bridge Local - Responsabilidades e Evolução Operacional

Data: 2026-06-12

## Contexto

Este documento registra a divisão correta entre a aplicação HelpUS AI e a infraestrutura AI Bridge Local, após os testes de conversa entre chats, uso do watcher e tentativa de treinamento operacional da nossa IA particular.

## Divisão de responsabilidades

### HelpUS AI (`D:/dev/ai`)

A pasta `D:/dev/ai` contém a aplicação da nossa IA particular. Esta frente é responsável por evoluir a capacidade da HelpUS AI, incluindo:

- comportamento do assistente;
- prompt base e instruções operacionais;
- autenticação e rotas do backend;
- integração com provedores de IA;
- entendimento do protocolo AI Bridge Local;
- capacidade de pedir dados faltantes antes de montar comandos;
- autonomia gradual para interagir com outros chats e, quando autorizado, solicitar execuções locais.

Toda evolução da inteligência, do comportamento e da autossuficiência da HelpUS AI deve acontecer nesta frente.

### AI Bridge Local (`D:/dev/autocode/ai-bridge-local`)

A pasta `D:/dev/autocode/ai-bridge-local` contém a infraestrutura local de transporte e execução. Esta frente é responsável por:

- conversa entre chats;
- entrega de mensagens via extensão;
- gateway local;
- worker local;
- execução de comandos no computador quando solicitada por envelopes válidos;
- validação, enfileiramento, recibos e telemetria local.

Esta frente não deve ser alterada pela frente HelpUS AI sem coordenação com o chat responsável pelo AI Bridge Local.

## Aprendizado importante do incidente

Durante os testes, a HelpUS AI confundiu recibos/logs do watcher com comandos de entrada.

Exemplo de recibo/log, que não é comando:

```text
[AI_LOCAL] id=... resultado=pendente metodo=watcher status=enviando
```

Esse tipo de texto é apenas a saída da extensão ou do bridge. A HelpUS AI não deve simular esse formato.

Quando o usuário pedir para usar o watcher, a HelpUS AI deve entender que precisa produzir um comando válido para o AI Bridge Local, e não um log.

## Regra operacional para a HelpUS AI

Quando receber instrução explícita para usar watcher, bridge ou AI Bridge Local:

1. Não escrever logs como `[AI_LOCAL]`, `[AI_LOCAL_RUN]`, `resultado=pendente`, `status=enviando` ou `metodo=watcher`.
2. Não simular recibos.
3. Se for conversa entre chats, usar ação `send-chat-message`.
4. Se for execução local, usar ação `run-command` somente quando houver dados suficientes e autorização.
5. Usar `delivery_kind` correto:
   - `inter_agent_message` para conversa entre chats;
   - `local_capability` para execução local via gateway/worker.
6. Se faltarem dados obrigatórios, pedir os dados em texto comum.
7. Se for instruída a responder via bridge, responder somente com o envelope solicitado, sem explicações antes ou depois.
8. Usar JSON estrito, aspas duplas ASCII e evitar caracteres invisíveis.
9. Não colocar exemplos de marcadores de envelope dentro de campos de mensagem enviados para outra IA, pois a extensão pode interpretar esses marcadores como um novo comando.
10. Não inventar `source_chat_id`, `target_chat_id`, `command_id`, `cwd` ou comandos locais quando não estiverem claros.

## Diretriz de evolução

A HelpUS AI deve ser treinada para ficar cada vez mais autossuficiente, mas a evolução deve ocorrer na aplicação `D:/dev/ai`, principalmente no prompt base e nas camadas de instrução do backend.

A infraestrutura AI Bridge Local deve permanecer como ferramenta de transporte/execução. Ela não deve carregar regras específicas da HelpUS AI, exceto quando definido pelo chat responsável pelo projeto AI Bridge Local.

## Procedimento recomendado para próximos ajustes

1. Inspecionar o prompt atual da HelpUS AI em `backend/cerebro.py`.
2. Adicionar uma seção curta e objetiva sobre uso do AI Bridge Local.
3. Validar sintaxe Python e diff.
4. Testar uma conversa normal para garantir que a HelpUS AI continua respondendo como assistente comum.
5. Testar uma instrução controlada de uso do watcher.
6. Só depois de validar, commitar e publicar.

## Estado registrado

- A alteração experimental feita no AI Bridge Local para criar um modo simples foi revertida.
- O commit de remoção no AI Bridge Local foi `4aea3cf Remove simple bridge mode changes`.
- A versão do `extension/content_script.js` voltou para `0.4.36`.
- A evolução futura da HelpUS AI deve ocorrer no repo `D:/dev/ai`.


---

## Fonte legacy: HELPUS_AI_HISTORY_AND_PROJECT_MEMORY_BACKLOG_2026-06-12.md

# HelpUS AI - Backlog de historico, continuidade e memoria ativa

Data: 2026-06-12
Repo: D:/dev/ai

## Contexto

Durante a evolucao da HelpUS AI, foi identificado que a aplicacao precisa melhorar dois pontos importantes para uso por desenvolvedores:

1. permitir ver mensagens e conversas anteriores com mais clareza;
2. permitir continuar uma conversa existente sem cair sempre em uma nova conversa;
3. adicionar memoria ativa do projeto, para preservar fatos operacionais, decisoes e proximos passos.

## Estado atual observado

O backend ja possui base de historico:

- MensagemRequest aceita session_id e project_id.
- O endpoint /chat usa session_id existente ou cria um novo.
- Antes de responder, o backend tenta carregar historico da session_id.
- A conversa e salva na tabela conversas com user_email, title e project_id.
- Existem endpoints /conversas, /historico/{session_id} e DELETE /conversa/{session_id}.

O frontend tambem ja possui partes relevantes:

- estado sessionId;
- lista conversas;
- carregarConversas;
- carregarHistorico;
- URL /c/{sessionId};
- botao Nova conversa;
- busca de chats;
- indicador de historico ativo.

Portanto, a proxima etapa nao e criar historico do zero. A etapa correta e melhorar a UX de continuidade, criar smokes especificos e adicionar memoria ativa do projeto.

## Atividade 1 - Continuidade de conversas anteriores

Objetivo: o usuario deve conseguir abrir uma conversa anterior, ver as mensagens ja feitas e continuar exatamente na mesma session_id.

Requisitos:

- abrir /c/{sessionId} deve carregar historico automaticamente;
- clicar em conversa recente deve carregar historico e manter session_id ativa;
- enviar nova mensagem depois de carregar historico deve usar a mesma session_id;
- botao Nova conversa deve ser claro e separado de continuar conversa;
- interface deve mostrar claramente qual conversa esta ativa;
- se o historico falhar, mostrar erro amigavel e manter opcao de tentar novamente;
- mobile deve ter acesso claro a chats recentes.

Validacoes desejadas:

- criar conversa nova;
- confirmar que aparece em /conversas;
- abrir /c/{session_id};
- confirmar que /historico/{session_id} retorna mensagens;
- enviar nova mensagem com a mesma session_id;
- confirmar que a conversa continua e nao cria nova session_id.

## Atividade 2 - Memoria ativa do projeto

Objetivo: criar uma camada persistente de memoria de projeto para desenvolvedores, separada do historico comum de conversas.

Essa memoria deve guardar fatos e decisoes como:

- divisao de responsabilidades entre HelpUS AI e AI Bridge Local;
- regras operacionais do watcher;
- IDs importantes quando apropriado;
- preferencias de desenvolvimento;
- estado atual das frentes;
- proximas atividades;
- decisoes tomadas pelo usuario;
- cuidados e restricoes para nao repetir erros.

Requisitos iniciais:

- tabela propria, por exemplo project_memories;
- campos sugeridos:
  - id;
  - project_id;
  - title;
  - content;
  - tags;
  - enabled;
  - created_at;
  - updated_at;
  - created_by;
- endpoints autenticados:
  - listar memorias;
  - criar memoria;
  - editar memoria;
  - desativar memoria;
  - buscar memorias por projeto/tag;
- painel no frontend para desenvolvedores verem e editarem memorias;
- uso controlado no prompt da HelpUS AI:
  - incluir somente memorias enabled;
  - limitar tamanho;
  - priorizar project_id atual;
  - deixar claro que memoria de projeto e contexto operacional, nao ordem absoluta.

## Cuidados

- memoria ativa nao deve substituir auditoria em Git/docs;
- memoria nao deve armazenar segredos, tokens, senhas ou credenciais;
- deve haver forma de editar/desativar memoria incorreta;
- deve haver separacao por usuario/projeto quando necessario;
- toda mudanca de comportamento sensivel deve continuar documentada em docs e commits.

## Ordem recomendada

1. Criar smoke/inspecao da continuidade de historico existente.
2. Corrigir UX de continuar conversa, se necessario.
3. Criar documentacao tecnica da memoria ativa.
4. Implementar backend da memoria ativa.
5. Implementar frontend da memoria ativa.
6. Integrar memoria ativa ao prompt com limite e filtros.
7. Criar smokes de memoria ativa.
8. Deploy controlado.

## Estado

Backlog registrado. Nenhuma alteracao de codigo foi aplicada neste documento.

---

## Fonte legacy: HELPUS_AI_OPERATIONAL_CLOSURE_2026-06-12.md

# HelpUS AI operational closure - 2026-06-12

## Validation completed

- Railway backend is online.
- Health endpoint /saude returned saudavel.
- Status endpoint returned online.
- Provider configured and used is deepseek.
- Active model is deepseek-chat.
- Internal smoke chat with token returned HTTP 200 using deepseek.
- Production smoke passed using the Vercel frontend URL.
- Frontend build passed.

## Domain note

- ai.helpusbr.com is valid in Vercel and works from mobile data.
- The local network resolves DNS but cannot connect to Vercel edge IPs on TCP 443.
- This is a local network or route issue, not a HelpUS backend, DeepSeek, or Vercel app issue.
- Until the local route is recovered, use the Vercel URL for smoke validation.

## Security note

- Rotate exposed operational secrets after this session because Railway variables were printed in a local command output.

## Current git reference

- Last relevant code commit: 74c61bf Enable HelpUS provider loop for DeepSeek primary.



---

## Fonte legacy: HELPUS_AI_OPERATIONAL_STATUS_2026-06-12.md

# HelpUS AI operational status - 2026-06-12

## Closed validation

- Backend Railway is online.
- Health endpoint /saude returns saudavel.
- Status endpoint reports provider configured/used as deepseek.
- Active model is deepseek-chat.
- Internal smoke chat with token returned HTTP 200 and provider_used=deepseek.
- Production smoke passed with the Vercel frontend URL.
- Frontend build passed.

## Domain note

- ai.helpusbr.com is valid in Vercel and worked from mobile data.
- The local network could resolve DNS but could not connect to the Vercel edge IPs on port 443.
- This is tracked as a local network/route/DNS issue, not a backend or application issue.
- Until the local route is recovered, use https://helpus-ai.vercel.app for smoke validation.

## Git reference

- Last relevant commit: 74c61bf Enable HelpUS provider loop for DeepSeek primary.



---

## Fonte legacy: HELPUS_AI_OPERATIONS.md

# HelpUS AI - Operacoes e proximas atividades

Atualizado em: 2026-06-11 18:52:30

Este e o documento principal da frente HelpUS AI. Os demais documentos markdown antigos da pasta docs foram movidos para docs/legacy para preservar historico sem fragmentar a operacao.

## Estado atual

- Frontend em producao: Vercel.
- Dominio publico oficial: https://ai.helpusbr.com.
- URL Vercel funcional para smoke/local: https://helpus-ai.vercel.app.
- Backend em producao: Railway.
- Backend publico: https://helpus-api-production.up.railway.app.
- Banco: Railway Postgres.
- Autenticacao: login Google obrigatorio para /chat.
- AUTH_REQUIRED=true em producao.
- Provider primario: DeepSeek.
- Fallback: Gemini e OpenRouter.
- Ordem de providers em producao: deepseek.
- Admin dashboard ativo em /admin.
- provider_used e fallback_reason ja existem no backend.
- Badge de provider existe no frontend, mas fica oculto por padrao e so aparece com debug local.
- Endpoint interno smoke-chat foi criado em backend/main.py e depende de INTERNAL_SMOKE_TOKEN.
- Documento principal: docs/HELPUS_AI_OPERATIONS.md.
- Docs historicos: docs/legacy.

## Commits recentes importantes

- 3cc08a0 Hide HelpUS provider badge by default
- 6aab764 Show HelpUS AI provider on responses
- 84966ef Protect HelpUS admin status endpoint
- f217cc6 Gate HelpUS admin dashboard by Google account
- ad307f3 Add HelpUS admin entrypoint to actions menu
- 5ef8375 Add HelpUS internal smoke chat and operations docs

## Arquitetura

Usuario -> Frontend Vercel -> Backend Railway -> Providers IA -> Postgres Railway.

Providers:
1. DeepSeek
2. Gemini
3. OpenRouter

Fluxo normal:
1. Usuario entra com Google.
2. Frontend salva helpus_google_token no navegador.
3. Frontend chama /chat com Authorization Bearer.
4. Backend valida token Google.
5. Backend chama provider IA.
6. Resposta retorna conteudo, provider_used e fallback_reason.

Fluxo tecnico:
1. Watcher chama /internal/smoke-chat.
2. Envia header x-internal-smoke-token.
3. Backend compara com INTERNAL_SMOKE_TOKEN.
4. Backend chama provider IA.
5. Retorna provider_configured, provider_used, fallback_reason, model e latency_ms.

## Variaveis de ambiente Railway

Obrigatorias ou relevantes:

- AUTH_REQUIRED=true
- GOOGLE_CLIENT_ID
- ADMIN_EMAILS
- AI_PROVIDER
- AI_PROVIDER_ORDER=deepseek
- DEEPSEEK_API_KEY
- DEEPSEEK_MODEL=deepseek-chat
- DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
- GEMINI_API_KEY
- OPENROUTER_API_KEY
- INTERNAL_SMOKE_TOKEN

Regras:
- Nunca imprimir tokens.
- Nunca colar token Google no chat.
- Nunca expor chaves em logs.
- Confirmar presenca de INTERNAL_SMOKE_TOKEN sem mostrar valor.

## Variaveis de ambiente Vercel

- NEXT_PUBLIC_API_URL=https://helpus-api-production.up.railway.app
- NEXT_PUBLIC_GOOGLE_CLIENT_ID
- NEXT_PUBLIC_ADMIN_EMAILS

## Endpoints

Publicos:
- GET /
- GET /saude
- GET /status

Com Google:
- POST /chat
- GET /admin/status

Interno:
- POST /internal/smoke-chat

O endpoint interno deve:
- retornar 401 sem token;
- retornar 401 se INTERNAL_SMOKE_TOKEN nao estiver configurado;
- retornar 401 com token invalido;
- nao logar token;
- nao salvar PII;
- retornar ok, resposta, provider_configured, provider_used, fallback_reason, model e latency_ms.

## Debug do provider no frontend

Ativar:

```js
localStorage.setItem('helpus_provider_debug', '1')
```

Desativar:

```js
localStorage.removeItem('helpus_provider_debug')
```

## Validacao obrigatoria

Antes de commit:

```powershell
git status -sb
python -m py_compile backend/main.py backend/auth.py backend/config.py backend/cerebro.py
npm --prefix frontend run build
npm run smoke:prod
git diff --check
git diff --stat
```

## Deploy backend Railway

```powershell
railway status
railway up -y -d --service helpus-api --environment production
Start-Sleep -Seconds 90
railway status
npm run smoke:prod
```

## Deploy frontend Vercel

Executar somente se houver mudanca de frontend ou env publica:

```powershell
npm --prefix frontend run build
vercel --prod
npm run smoke:prod
```

## Smoke interno via watcher

1. Confirmar que INTERNAL_SMOKE_TOKEN existe no Railway sem imprimir valor.
2. Chamar /internal/smoke-chat sem token e esperar 401.
3. Chamar /internal/smoke-chat com token e esperar ok=true.
4. Confirmar provider_used=deepseek.
5. Confirmar fallback_reason=null ou documentar fallback.
6. Confirmar latency_ms presente.

## Status conhecido

- helpus-api online.
- Frontend online.
- Smoke prod OK em validacoes recentes.
- Railway pode mostrar deploy failed antigo no recurso postgres-volume. Monitorar, mas nao tratar como falha se backend e smoke estiverem OK.

## Proximas atividades

Prioridade 1:
- Configurar ou confirmar INTERNAL_SMOKE_TOKEN no Railway.
- Fazer deploy Railway do commit com endpoint interno.
- Testar 401 sem token.
- Testar OK com token.
- Confirmar provider_used=deepseek.

Prioridade 2:
- Melhorar admin dashboard com metricas de provider:
  - provider configurado;
  - provider usado;
  - fallback_reason;
  - model;
  - latency_ms;
  - status do smoke interno sem expor token.

Prioridade 3:
- Persistir metricas por request:
  - data;
  - provider;
  - latencia;
  - sucesso;
  - fallback_reason;
  - tokens se disponiveis.

Prioridade 4:
- Criar feedback de resposta:
  - util;
  - nao util;
  - comentario;
  - motivo.

Prioridade 5:
- Implementar RAG com documentos HelpUS, FAQs, politicas e base de conhecimento.

Prioridade 6:
- Memoria persistente por usuario e projeto com controles de privacidade.

## Politica de docs

- HELPUS_AI_OPERATIONS.md e o unico documento principal em docs.
- Outros markdowns ficam em docs/legacy.
- Nao apagar historico sem aprovacao explicita.
- Toda decisao operacional relevante deve ser atualizada aqui.

## Checklist final de frente pronta

- git status limpo;
- build OK;
- smoke OK;
- Railway online;
- Vercel online se alterado;
- internal smoke 401 sem token;
- internal smoke OK com token;
- provider_used deepseek confirmado;
- docs atualizados;
- nenhum segredo exposto.


---

## Fonte legacy: HELPUS_AI_OPERATIONS_DELTA_2026-06-12.md

# HelpUS AI operations delta - 2026-06-12

## Current production state

- AI_PROVIDER=deepseek.
- AI_PROVIDER_ORDER=deepseek.
- DEEPSEEK_MODEL=deepseek-chat.
- Backend health and status endpoints returned HTTP 200.
- Status endpoint reported provider_order=[deepseek], provider_configured=deepseek, provider_used=deepseek.
- Production smoke passed using the Vercel frontend URL.

## Frontend domain note

- Official public domain: https://ai.helpusbr.com.
- Functional smoke/local URL: https://helpus-ai.vercel.app.
- ai.helpusbr.com is valid in Vercel and works from mobile data.
- The current local network resolves DNS but cannot connect to Vercel edge IPs on TCP 443.
- Treat this as a local network route/DNS issue until proven otherwise.

## Follow-up

- Rotate Railway secrets that were printed during local diagnostics.
- Keep smoke default on the Vercel URL while the local network issue persists.



---

## Fonte legacy: HELPUS_CHAT_WATCHER_INTELLIGENCE_ROADMAP.md

# HelpUS Chat Watcher Intelligence Roadmap

## Objetivo

Tornar o chat HelpUS mais inteligente, independente e seguro ao interpretar, propor e acompanhar comandos via watcher / AI Bridge Local.

## Estado atual seguro

- Repo principal: D:/dev/ai
- Branch: main
- Remoto: origin/main
- Protocolos existentes: HELPUS_AGENT_OPERATING_PROTOCOL.md, HELPUS_WATCHER_COMMAND_PROTOCOL.md e HELPUS_OPERATIONAL_AUTOMATION.md.
- Smokes existentes: smoke_operational_release.py, smoke_health_report.py, smoke_agent_operating_protocol.py e smoke_watcher_command_protocol.py.

## Problema que falta resolver

Os documentos e smokes existem, mas o chat ainda precisa de uma camada explicita de inteligencia operacional para consultar esses protocolos antes de responder pedidos como prossiga, continue, use o watcher, corrija e reenvie, o comando falhou, quais as proximas atividades e deixe o chat independente.

Sem essa camada, o chat pode depender demais do historico da conversa e pode voltar a confundir recibos do watcher com comandos de entrada.

## Ordem recomendada para comecar

### Micro 24 - Contexto operacional do agente

Criar modulo backend que carregue os docs operacionais e entregue um resumo seguro para o chat.

Arquivos provaveis:
- backend/operational_context.py
- scripts/watcher/smoke_operational_context.py
- scripts/watcher/smoke_operational_release.py
- scripts/watcher/health_report.py

Criterio de pronto: modulo carrega docs obrigatorios, smoke confirma marcadores essenciais, suite operacional passa, health report passa, build frontend passa e git diff --check passa.

### Micro 25 - Intencao watcher

Criar classificador simples para entender pedidos relacionados ao watcher.

Categorias minimas: inspect, patch, validate, commit, tag, recover e stop.

Arquivos provaveis:
- backend/watcher_intent.py
- scripts/watcher/smoke_watcher_intent.py

Criterio de pronto: smoke cobre frases reais do operador, nao trata AI_LOCAL_RUN ou AI_LOCAL_ERRO como comando novo e sabe quando resumir resultado ou propor envelope novo.

### Micro 26 - Builder seguro de envelopes watcher

Criar gerador de envelopes watcher com JSON estrito e regras de seguranca.

Regras obrigatorias: command_id novo, payload.cwd explicito, payload.command como array, marcadores locais sozinhos nas linhas, evitar inline grande e nunca repetir o mesmo envelope apos envelope_parse_error.

Arquivos provaveis:
- backend/watcher_envelope_builder.py
- scripts/watcher/smoke_watcher_envelope_builder.py

### Micro 27 - Recuperacao de erros watcher

Criar rotina para interpretar falhas e propor recuperacao segura.

Entradas: envelope_parse_error, return_code diferente de zero, erro de build, erro de smoke, erro de git diff --check, arquivo inesperado modificado e repo sujo antes de patch.

Arquivos provaveis:
- backend/watcher_recovery.py
- scripts/watcher/smoke_watcher_recovery.py

### Micro 28 - Integracao com resposta do chat

Integrar contexto operacional, intencao watcher, builder e recuperacao no fluxo real de resposta.

Objetivo: quando o usuario disser prossiga ou continue, o chat consulta contexto, escolhe micro seguro e propoe comando watcher valido. Quando receber recibo, resume resultado e escolhe proximo passo. Quando receber erro, corrige sem repetir o erro. Quando houver risco, para e pede autorizacao.

## Validacoes obrigatorias antes de cada commit

Executar sempre:
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check

## Regras de seguranca

- Nao fazer deploy sem autorizacao explicita.
- Nao usar git reset --hard, git clean, remocoes em massa, migracoes destrutivas ou alteracao de secrets sem dry-run e autorizacao.
- Nao commitar se houver arquivo inesperado modificado.
- Nao criar tag se o repo nao estiver limpo.
- Em erro de parse de envelope, considerar que nada foi executado e gerar command_id novo.
- Em falha parcial, inspecionar antes de corrigir.

## Criterio de independencia do chat

O chat sera considerado mais independente quando conseguir consultar docs operacionais automaticamente, identificar a tarefa correta sem depender de historico manual longo, diferenciar recibo erro e pedido novo, propor envelopes JSON validos, corrigir erro de parse sem repetir o erro, validar com suite real, resumir resultado e recomendar o proximo micro.

### Micro 29 - Provedor local/offline de IA

Adicionar suporte opcional a um runtime local de IA, como LM Studio ou outro servidor compativel com API local, para apoiar raciocinio operacional privado e modo offline/degradado.

Objetivo:

- consultar docs e protocolos operacionais localmente;
- resumir estado do repo sem depender de provedor externo;
- classificar intencoes watcher com mais privacidade;
- interpretar recibos e erros sem enviar logs sensiveis para fora;
- manter execucao real sempre via watcher;
- manter fallback para provedores externos quando configurado.

Arquivos provaveis:

- backend/local_ai_provider.py
- backend/operational_context.py
- scripts/watcher/smoke_local_ai_provider.py
- docs/HELPUS_LOCAL_AI_PROVIDER.md

Criterio de pronto: runtime local opcional, falha segura quando indisponivel, nenhum segredo exposto, smokes verdes, health report verde, build frontend verde e git diff --check verde.


---

## Fonte legacy: HELPUS_LOCAL_AI_PROVIDER.md

# HelpUS Local AI Provider

## Objetivo

Documentar a frente de provedor local/offline de IA para tornar o HelpUS mais independente, privado e resiliente quando houver falha ou indisponibilidade de provedores externos.

## Ideia central

O HelpUS pode usar um runtime local de IA, como LM Studio, Ollama ou outro servidor compativel com API local, para tarefas operacionais que nao exigem internet.

Essa camada nao substitui o watcher. O watcher continua sendo o mecanismo seguro de execucao local. O provedor local ajuda o chat a pensar, resumir documentos, interpretar recibos, classificar intencoes e propor proximos micros com mais privacidade.

## Beneficios esperados

- Reduzir dependencia de internet para analise operacional.
- Evitar envio de docs, logs e arquivos sensiveis para provedores externos quando nao for necessario.
- Permitir modo degradado/offline para leitura de docs, resumo de estado e classificacao de intencoes watcher.
- Usar os protocolos operacionais como prompt/contexto local.
- Manter fallback para provedores externos quando configurado e autorizado.

## Limites importantes

- O provedor local nao deve executar comandos diretamente.
- Execucao continua passando pelo watcher / AI Bridge Local.
- O modelo local pode errar; portanto toda acao deve continuar validada por smokes, build e git diff --check.
- Se o runtime local estiver indisponivel, a aplicacao nao deve quebrar.
- Nenhum segredo deve ser impresso em logs ou enviado a modelos externos sem autorizacao.

## Micro 29 - Provedor local/offline de IA

Arquivos provaveis:

- backend/local_ai_provider.py
- backend/operational_context.py
- scripts/watcher/smoke_local_ai_provider.py
- docs/HELPUS_LOCAL_AI_PROVIDER.md

Criterio de pronto:

- smoke valida configuracao local sem exigir internet;
- app nao quebra se o provedor local estiver indisponivel;
- fallback atual continua funcionando;
- nenhum segredo e exposto;
- suite operacional passa;
- health report passa;
- build frontend passa;
- git diff --check passa.

## Uso operacional esperado

Quando o usuario pedir continuidade, analise de docs, resumo de estado ou interpretacao de recibos watcher, o HelpUS deve consultar primeiro o contexto operacional local. Se houver runtime local disponivel, ele pode ser usado para apoio analitico.

Quando a tarefa envolver execucao, patch, commit, tag, deploy ou alteracao sensivel, o HelpUS deve continuar usando o fluxo seguro: contexto operacional, classificacao de intencao, builder de envelope, watcher, validacao real e resumo do resultado.

## Configuracao futura sugerida

Variaveis provaveis:

- HELPUS_LOCAL_AI_ENABLED=false
- HELPUS_LOCAL_AI_BASE_URL=http://localhost:1234/v1
- HELPUS_LOCAL_AI_MODEL=local-model
- HELPUS_LOCAL_AI_TIMEOUT_SECONDS=60

A configuracao deve ser opcional e segura por padrao.


---

## Fonte legacy: HELPUS_OPERATIONAL_AUTOMATION.md

# HelpUS AI - Automacao operacional

## Estado atual

A frente operacional da HelpUS AI possui validacoes automatizadas para reduzir comandos quebrados, erros de envelope watcher e regressao em memorias/projetos.

## Validacoes implementadas

1. Intent layer e command builder: validam send_chat e run_command antes do envio.
2. Behavior smoke: cobre contrato operacional do prompt, builder e preflight.
3. Watcher error classifier: classifica falhas parse, semantic, delivery, timeout e unknown.
4. Telemetria local: registra eventos JSONL simples para diagnostico.
5. Command safety: detecta comandos destrutivos e exige dry-run ou autorizacao explicita.
6. Watcher stress smoke: exercita envelopes validos e invalidos em volume.
7. Memory panel contract smoke: protege marcadores essenciais do painel de memorias.

## Suite recomendada

powershell
python -m py_compile backend/main.py backend/banco.py backend/cerebro.py backend/command_builder.py backend/preflight_validator.py backend/intent_layer.py backend/watcher_errors.py backend/telemetry.py backend/command_safety.py scripts/watcher/smoke_behavior_ai.py scripts/watcher/smoke_intent_layer.py scripts/watcher/smoke_watcher_errors.py scripts/watcher/smoke_telemetry.py scripts/watcher/smoke_command_safety.py scripts/watcher/smoke_watcher_stress.py scripts/watcher/smoke_memory_panel_contract.py
python scripts/watcher/smoke_behavior_ai.py
python scripts/watcher/smoke_intent_layer.py
python scripts/watcher/smoke_watcher_errors.py
python scripts/watcher/smoke_telemetry.py
python scripts/watcher/smoke_command_safety.py
python scripts/watcher/smoke_watcher_stress.py
python scripts/watcher/smoke_memory_panel_contract.py
npm --prefix frontend run build
git diff --check


## Proximas frentes

- Integrar telemetria ao painel admin.
- Criar smoke unico de release operacional.
- Criar relatorio de saude local com ultimos commits, status, build e smokes.
- Evoluir painel de memorias com busca, tags e historico de alteracoes.
- Preparar tag de release apenas apos suite completa verde.

## Release smoke e health report

A suite operacional agora tambem possui dois utilitarios de fechamento:

- scripts/watcher/smoke_operational_release.py: executa a suite operacional principal em uma chamada unica.
- scripts/watcher/health_report.py: gera reports/helpus_health_report.json com status git, HEAD, log recente e existencia dos smokes.
- scripts/watcher/smoke_health_report.py: valida a geracao e o contrato minimo do health report.

## Comando final recomendado antes de tag

powershell
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check
git status -sb


## Criterio para tag operacional

Criar tag somente quando release smoke, health report, build frontend e diff check estiverem verdes com repo limpo/alinhado.

## Baseline admin telemetry UI - 2026-06-13

Ponto seguro criado apos integrar telemetria operacional ao painel admin.

- Tag: helpus-admin-telemetry-ui-2026-06-13
- Commit: eebdc82 Add admin telemetry card to operational panel
- Backend: GET /admin/telemetry protegido por obter_admin_google e baseado em summarize_events.
- Frontend: /admin exibe o card Telemetria operacional usando /admin/telemetry.
- Smokes adicionados: smoke_admin_telemetry_route_contract.py e smoke_admin_telemetry_ui_contract.py.
- Suite agregada: smoke_operational_release.py inclui os contratos de rota e UI.
- Health report: health_report.py lista os smokes de telemetria admin.

### Validacao obrigatoria antes de novas alteracoes

Executar, nesta ordem:

powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check


### Criterio de continuidade

Prosseguir apenas se a suite operacional, health report, build frontend e diff check estiverem verdes. Se houver alteracoes locais inesperadas, parar e inspecionar antes de aplicar qualquer patch.

### Proximas frentes recomendadas

1. Inspecao visual/manual do painel /admin em ambiente local ou producao.
2. Melhorar o resumo de telemetria com ultimos eventos, ultima falha e timestamp mais recente.
3. Adicionar smoke de contrato para novos campos antes de expor na UI.
4. Manter commits pequenos, com uma frente por vez e sem deploy automatico.


---

## Fonte legacy: HELPUS_WATCHER_COMMAND_PROTOCOL.md

# HelpUS Watcher Command Protocol

Este documento define como o chat HelpUS deve entender, propor e acompanhar comandos via watcher/AI Bridge Local sem confundir recibos com comandos.

## Objetivo

Tornar o agente capaz de usar o watcher com seguranca operacional, entendendo quando deve apenas interpretar logs, quando deve propor um envelope novo e quando deve parar por risco ou erro de parse.

## Conceitos obrigatorios

O agente deve diferenciar tres coisas:

1. Pedido do usuario: uma instrucao em linguagem natural.
2. Envelope watcher: JSON valido enviado entre marcadores locais.
3. Recibo watcher: resposta como `[AI_LOCAL]`, `[AI_LOCAL_RUN]` ou `[AI_LOCAL_ERRO]`.

Recibos nao sao comandos de entrada. O agente deve analisar o resultado e propor o proximo passo.

## Marcadores locais

Quando precisar enviar um envelope ao watcher, usar marcadores sozinhos nas linhas:

```text
@@AI_BRIDGE_LOCAL_START@@
{ JSON valido aqui }
@@AI_BRIDGE_LOCAL_END@@
```

Nao colocar texto extra na mesma linha dos marcadores.

## Campos minimos do envelope

Um envelope seguro deve conter:

- `command_id`: identificador unico e descritivo.
- `action`: normalmente `run-command`.
- `source_chat_id`: chat de origem.
- `target_chat_id`: destino do watcher.
- `delivery_kind`: normalmente `local_capability`.
- `conversation_id`: frente operacional.
- `from_agent`: quem solicitou.
- `payload.cwd`: diretorio de trabalho.
- `payload.timeout_seconds`: timeout.
- `payload.command`: lista de argumentos do processo.

## Modelo seguro de envelope

```json
{
  "command_id": "helpus_inspect_example_001",
  "action": "run-command",
  "source_chat_id": "CURRENT_CHAT_ID",
  "target_chat_id": "gateway-brain-supervisor",
  "delivery_kind": "local_capability",
  "conversation_id": "helpus_safe_inspection",
  "from_agent": "Wagner supervisor",
  "payload": {
    "cwd": "D:/dev/ai",
    "timeout_seconds": 300,
    "command": [
      "powershell",
      "-NoProfile",
      "-Command",
      "Write-Output 'START'; git status -sb; Write-Output 'END'"
    ]
  }
}
```

## Regras para montar comandos

1. Usar `payload.command` como array JSON, nao como string solta.
2. Usar aspas duplas ASCII no JSON.
3. Evitar aspas curvas, caracteres invisiveis e comandos inline grandes.
4. Para comando grande, preferir script pequeno real ou `python -c` com base64 ASCII.
5. Evitar `$.Name` em PowerShell; usar `$PSItem.Name` ou `$_.Name`.
6. Evitar `python -c` com blocos multiline sem indentacao controlada.
7. Preferir inspecao antes de patch.
8. Nunca misturar dry-run e execucao destrutiva no mesmo comando.
9. Sempre imprimir marcadores de inicio e fim.
10. Sempre validar `git status -sb` no inicio e no fim.

## Como interpretar resultados

### `[AI_LOCAL_RUN] status=acked return_code=0`

Significa que o comando executou com sucesso. O agente deve resumir:
- o que foi feito;
- validacoes que passaram;
- commit/tag se houver;
- estado final do repo;
- proximo micro recomendado.

### `[AI_LOCAL_RUN] status=failed`

Significa que o comando executou e falhou. O agente deve:
- identificar causa provavel;
- dizer se houve alteracao parcial;
- propor comando de inspecao/recuperacao;
- nao repetir o mesmo erro.

### `[AI_LOCAL_ERRO] envelope_parse_error`

Significa que nada foi executado. O agente deve:
- corrigir JSON;
- trocar `$.Name` por `$PSItem.Name` quando aplicavel;
- evitar inline grande;
- reenviar com `command_id` novo;
- se havia delete/move/clean, reenviar primeiro em dry-run/listagem.

## Rotina watcher para cada tarefa

1. Classificar a tarefa: inspecao, patch, validacao, tag ou deploy.
2. Para inspecao: comando somente leitura.
3. Para patch: alterar poucos arquivos e validar.
4. Para validacao: rodar suite real.
5. Para tag: exigir repo limpo.
6. Para deploy: exigir autorizacao explicita.
7. Em erro: parar, resumir e propor recuperacao.

## Comandos reais de validacao do repo

```powershell
git status -sb
python scripts/watcher/smoke_operational_release.py
python scripts/watcher/smoke_health_report.py
npm --prefix frontend run build
git diff --check
```

## Comandos destrutivos ou sensiveis

Exigem dry-run, explicacao e autorizacao explicita:

- `git reset --hard`
- `git clean -fd` ou `git clean -fdx`
- `git push --force`
- remocoes em massa
- migracoes destrutivas de banco
- alteracao de secrets
- deploy

## Como propor proximos passos

O agente deve propor proximos micros pequenos, por exemplo:

- Micro A: inspecionar estado.
- Micro B: aplicar patch minimo.
- Micro C: validar e commit.
- Micro D: criar tag segura.

Cada micro deve ter objetivo, arquivos provaveis, risco, validacoes e criterio de pronto.

## Criterio de pronto

O chat entende o watcher quando consegue:

- nao confundir recibos com comandos;
- corrigir envelope parse error;
- montar JSON estrito;
- escolher comandos seguros;
- validar com a suite real;
- parar quando houver risco;
- relatar resultado final com proximo passo.

## Relacao com provedor local de IA

O provedor local de IA pode ajudar a interpretar contexto, recibos e erros, mas nao deve executar comandos.

Fluxo correto:

1. Provedor local ou contexto operacional ajuda a analisar.
2. watcher_intent classifica a tarefa.
3. watcher_envelope_builder gera envelope JSON seguro.
4. watcher / AI Bridge Local executa.
5. smokes, build e git diff --check validam.
6. chat resume o resultado e recomenda o proximo micro.

Componentes planejados relacionados:

- operational_context
- local_ai_provider
- watcher_intent
- watcher_envelope_builder
- watcher_recovery


## Fechamento final 2026-06-14

Status final: Micros 24 a 29 concluidos, validados, commitados e enviados para origin/main. HEAD pos-Micro 29: 96e3500 Add HelpUS local AI provider guardrails.

Entregas finais: Micro 27 watcher_recovery, Micro 28 chat_watcher_orchestrator, Micro 29 local_ai_provider, suite operacional, health report e build frontend.

Validacoes finais esperadas: py_compile, smoke_operational_release, smoke_health_report, npm --prefix frontend run build e git diff --check.

Regras permanentes: AI_LOCAL, AI_LOCAL_RUN e AI_LOCAL_ERRO sao recibos; parse error exige command_id novo e envelope simples; falha parcial exige inspecao antes de patch; IA local e analysis_only; sem deploy, reset hard, git clean, secrets, tags ou remocoes em massa sem autorizacao.

## Release and deploy decision gate

Release, tag and deploy are now tracked in docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md. These actions remain separated from development and require explicit human authorization.

## Watcher operations runbook

Daily safe operation is now tracked in docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md. The runbook defines inspection-first work, receipt handling, validation sequence and forbidden actions without explicit authorization.

## Post completion backlog

Future work after completion is tracked in docs/HELPUS_POST_COMPLETION_BACKLOG.md. The backlog is planning only and keeps release, deploy, hardening and product follow-up separated from completed work.

## Active documentation index

Active documentation is indexed in docs/README.md. The active set is the master document, release and deploy checklist, watcher operations runbook, post completion backlog and final report. Historical documents remain in docs/legacy.
