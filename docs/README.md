# Docs - HelpUS AI

Esta pasta concentra a documentacao operacional e tecnica do HelpUS AI.

Arquivos principais:

- HELPUS_AI_OVERVIEW.md: visao geral da aplicacao, arquitetura, recursos e status.
- HELPUS_AI_ROADMAP.md: proximas etapas planejadas.
- HELPUS_AI_OPERATIONS.md: comandos de build, smoke, deploy e validacao.
- PRODUCTION_CHECKLIST.md: checklist de producao ja existente.

<!-- HELPUS_MULTI_PROVIDER_FALLBACK_STATUS_20260608 -->

## Multi-provider fallback status - 2026-06-08

Implemented fallback Gemini -> OpenRouter -> DeepSeek. Default AI_PROVIDER_ORDER=gemini,openrouter,deepseek. Added scripts/30_smoke_ai_providers.py and npm run smoke:providers. Added docs/AI_PROVIDER_FALLBACK.md and provider key guards. Validated py_compile, smoke:providers, smoke:prod, and git diff --check. Anonymous production /chat returned expected HTTP 401 because Google ID token auth is required. Pending: finalize scripts/31_smoke_prod_chat.js, publish smoke:chat, test with token, add provider_used and fallback_reason observability, refactor fallback loop from AI_PROVIDER_ORDER, fix backend/main.py encoding, and keep docs updated.
