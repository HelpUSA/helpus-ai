# AI Provider Fallback

Status: implemented and validated.

## Runtime order

Default: gemini,openrouter,deepseek

Flow: Gemini first, then OpenRouter, then DeepSeek.

## Required variables

- GEMINI_API_KEY
- GEMINI_MODEL
- OPENROUTER_API_KEY
- OPENROUTER_MODEL
- DEEPSEEK_API_KEY
- DEEPSEEK_MODEL
- DEEPSEEK_API_URL
- AI_REVIEW_TIMEOUT

## Validation

Run:
- npm run smoke:providers
- npm run smoke:prod
- python -m py_compile backend/config.py backend/cerebro.py backend/main.py scripts/30_smoke_ai_providers.py

Expected provider smoke output: HELPUS_PROVIDER_CONFIG_SMOKE_OK

## Failure behavior

- If Gemini fails, OpenRouter is attempted.
- If OpenRouter fails or OPENROUTER_API_KEY is absent, DeepSeek is attempted.
- If DEEPSEEK_API_KEY is absent, the request fails explicitly.

Do not log API keys or full provider responses in production logs.

<!-- HELPUS_MULTI_PROVIDER_FALLBACK_STATUS_20260608 -->

## Multi-provider fallback status - 2026-06-08

Implemented fallback Gemini -> OpenRouter -> DeepSeek. Default AI_PROVIDER_ORDER=gemini,openrouter,deepseek. Added scripts/30_smoke_ai_providers.py and npm run smoke:providers. Added docs/AI_PROVIDER_FALLBACK.md and provider key guards. Validated py_compile, smoke:providers, smoke:prod, and git diff --check. Anonymous production /chat returned expected HTTP 401 because Google ID token auth is required. Pending: finalize scripts/31_smoke_prod_chat.js, publish smoke:chat, test with token, add provider_used and fallback_reason observability, refactor fallback loop from AI_PROVIDER_ORDER, fix backend/main.py encoding, and keep docs updated.
