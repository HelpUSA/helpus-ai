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
