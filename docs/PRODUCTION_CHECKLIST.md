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