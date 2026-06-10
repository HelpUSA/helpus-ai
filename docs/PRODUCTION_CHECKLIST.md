# HelpUS AI - Checklist de Producao

## Status atual

- Frontend em Vercel: https://ai.helpusbr.com
- Backend em Railway: https://helpus-api-production.up.railway.app
- Banco: Railway PostgreSQL
- Login: Google OAuth
- IA: Gemini
- Historico: por usuario autenticado
- Admin/status: /admin
- Busca web: DuckDuckGo HTML
- Clima: wttr.in com normalizacao de cidades brasileiras

## Variaveis Railway

Obrigatorias no servico helpus-api:

- ENVIRONMENT=production
- AI_PROVIDER=gemini
- GEMINI_API_KEY configurada no Railway
- GEMINI_MODEL=gemini-2.5-flash-lite
- DATABASE_URL apontando para o Postgres do Railway
- AUTH_REQUIRED=true
- GOOGLE_CLIENT_ID igual ao Client ID OAuth usado no frontend
- CORS_ORIGINS contendo https://ai.helpusbr.com

## Variaveis Vercel

Obrigatorias no projeto frontend:

- NEXT_PUBLIC_API_URL=https://helpus-api-production.up.railway.app
- NEXT_PUBLIC_GOOGLE_CLIENT_ID igual ao Client ID OAuth usado no backend

## Google OAuth

No OAuth Client usado pelo HelpUS AI, conferir Authorized JavaScript origins:

- https://ai.helpusbr.com
- http://localhost:3000

Nao usar API Key, Service Account nem Client Secret no frontend.

## Testes minimos pos-deploy

Backend:

- GET https://helpus-api-production.up.railway.app/saude
- GET https://helpus-api-production.up.railway.app/status

Frontend:

- Abrir https://ai.helpusbr.com
- Abrir https://ai.helpusbr.com/admin
- Login Google funciona
- Chat bloqueia sem login
- Chat responde apos login
- Historico lista conversas por usuario
- Apagar conversa funciona
- Busca web ligada retorna fontes
- Clima em Joao Pessoa retorna wttr.in e local normalizado

## Seguranca

- Nunca versionar .env, .env.local ou chaves reais.
- Nunca colocar GEMINI_API_KEY no frontend.
- NEXT_PUBLIC_GOOGLE_CLIENT_ID e publico e pode aparecer no navegador.
- CORS deve permanecer restrito em producao.
- AUTH_REQUIRED deve ficar true em producao.
- Verificar periodicamente npm audit.
- Nao rodar npm audit fix --force se tentar rebaixar Next para versao antiga.

## Comandos uteis

Backend health:

    $api = "https://helpus-api-production.up.railway.app"
    Invoke-RestMethod "$api/saude" | ConvertTo-Json -Depth 5
    Invoke-RestMethod "$api/status" | ConvertTo-Json -Depth 5

Deploy backend:

    railway service
    railway up

Deploy frontend:

    vercel --prod
Smoke Node versionado:

 npm run smoke:prod

## Multi-provider fallback checklist

- Confirm AI_PROVIDER_ORDER=gemini,openrouter,deepseek.
- Confirm GEMINI, OPENROUTER and DEEPSEEK keys are configured in production.
- Run npm run smoke:providers before deploy validation.
- Run npm run smoke:prod after deploy.
- npm run smoke:chat is published. Without HELPUS_GOOGLE_ID_TOKEN it must print CHAT_SMOKE_SKIPPED_AUTH_REQUIRED and exit 0; with a valid token, run it to validate authenticated /chat.
- Treat anonymous /chat HTTP 401 as expected when AUTH_REQUIRED=true.
- Do not log API keys, prompts, full provider responses, or bearer tokens.

<!-- HELPUS_MULTI_PROVIDER_FALLBACK_STATUS_20260608 -->

## Multi-provider fallback status - 2026-06-08

Implemented fallback Gemini -> OpenRouter -> DeepSeek. Default AI_PROVIDER_ORDER=gemini,openrouter,deepseek. Added scripts/30_smoke_ai_providers.py and npm run smoke:providers. Added scripts/31_smoke_prod_chat.js and npm run smoke:chat. Validated py_compile, smoke:providers, smoke:prod, smoke:chat without token, and git diff --check. Anonymous production /chat returned expected HTTP 401 because Google ID token auth is required. Added safe /chat response metadata provider_used and fallback_reason. Encoding for backend/main.py, backend/cerebro.py and backend/config.py was verified clean on 2026-06-10. Pending: keep fallback unit tests updated with provider changes, perform manual mobile validation, and keep docs updated.

## Status endpoint metadata checklist - 2026-06-08

- After deploy, call /status and confirm app_version is present.
- Confirm build_commit is present and matches the expected deployed commit when configured.
- Confirm auth_required is present and true in production.
- Confirm provider_order is present and matches gemini,openrouter,deepseek.
- Do not expose API keys, bearer tokens, prompts, or full provider responses in /status.
- If /status still shows only the old fields, treat it as deploy propagation pending and retry later.
