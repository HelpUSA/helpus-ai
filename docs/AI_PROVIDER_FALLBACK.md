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
