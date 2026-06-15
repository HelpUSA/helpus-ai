# HelpUSAI Provider Setup

Updated: 2026-06-15

## Problem observed

The chat UI returned provider failure:

- Erro ao conectar com o servidor.
- Todos os providers de IA falharam: deepseek

## Diagnosis

The HelpUSAI operational chain is complete through v0.29.0-dev, but the backend needs at least one working AI provider configured.

Readonly diagnosis found provider code in:

- backend/config.py
- backend/cerebro.py
- backend/main.py
- frontend/src/app/page.tsx

The local backend/.env contained DATABASE_URL and MODEL_PATH, but no visible provider variables.

## Configure one provider

Never commit real API keys. Keep secrets only in local env files or deployment variables.

### DeepSeek example

AI_PROVIDER=deepseek
AI_PROVIDER_ORDER=deepseek
DEEPSEEK_API_KEY=replace_with_real_secret
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions

### Gemini example

AI_PROVIDER=gemini
AI_PROVIDER_ORDER=gemini,deepseek
GEMINI_API_KEY=replace_with_real_secret
GEMINI_MODEL=gemini-2.5-flash-lite

### OpenRouter example

AI_PROVIDER=openrouter
AI_PROVIDER_ORDER=openrouter,deepseek
OPENROUTER_API_KEY=replace_with_real_secret
OPENROUTER_MODEL=openrouter/auto

## Local verification without printing secrets

Run after setting provider variables and restarting backend:

Set-Location "D:/dev/ai"
git status -sb
git status -s
Select-String -Path "backend/.env" -Pattern "AI_PROVIDER|AI_PROVIDER_ORDER|DEEPSEEK|GEMINI|OPENROUTER"

Only verify variable names and presence. Do not print or paste secret values.

## Expected result

The HelpUSAI chat should answer instead of returning provider failure.

If the error persists, inspect backend logs and provider HTTP status without exposing API keys.
