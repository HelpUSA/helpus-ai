# HelpUS AI - Operacoes

## Fluxo recomendado para mudancas

1. Fazer uma alteracao pequena.
2. Rodar build.
3. Rodar smoke.
4. Revisar diff.
5. Commitar.
6. Fazer push.
7. Fazer deploy.
8. Rodar smoke novamente.
9. Conferir producao manualmente.

## Comandos principais

Build frontend:

bash
npm run build


Smoke de producao:

bash
npm run smoke:prod


Deploy frontend:

bash
vercel --prod


Deploy backend:

bash
railway up


Validacao Python:

bash
python -m py_compile backend/config.py backend/banco.py backend/cerebro.py backend/buscador.py backend/auth.py backend/main.py


Status Git:

bash
git status -sb
git log --oneline -8


## Endpoints de saude

Backend:

- GET https://helpus-api-production.up.railway.app/saude
- GET https://helpus-api-production.up.railway.app/status

Frontend:

- GET https://ai.helpusbr.com
- GET https://ai.helpusbr.com/admin

## Smoke test

Arquivo:

text
scripts/29_smoke_prod.js


Comando:

bash
npm run smoke:prod


O smoke valida:

- API /saude.
- API /status.
- Frontend /.
- Frontend /admin.

Saida esperada:

text
OK saude
OK status
OK front
OK admin
HELPUS_SMOKE_OK


## Deploy atual

O frontend e publicado na Vercel e recebe alias em https://ai.helpusbr.com . O backend e publicado na Railway em https://helpus-api-production.up.railway.app.

## Checklist rapido antes de commit

- npm run build passou.
- npm run smoke:prod passou.
- git diff --check sem erros.
- Nenhuma chave real foi adicionada.
- Mudanca esta limitada ao escopo esperado.

<!-- HELPUS_MULTI_PROVIDER_FALLBACK_STATUS_20260608 -->

## Multi-provider fallback status - 2026-06-08

Implemented fallback Gemini -> OpenRouter -> DeepSeek. Default AI_PROVIDER_ORDER=gemini,openrouter,deepseek. Added scripts/30_smoke_ai_providers.py and npm run smoke:providers. Added docs/AI_PROVIDER_FALLBACK.md and provider key guards. Validated py_compile, smoke:providers, smoke:prod, and git diff --check. Anonymous production /chat returned expected HTTP 401 because Google ID token auth is required. Pending: finalize scripts/31_smoke_prod_chat.js, publish smoke:chat, test with token, add provider_used and fallback_reason observability, refactor fallback loop from AI_PROVIDER_ORDER, fix backend/main.py encoding, and keep docs updated.
